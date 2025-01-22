from functools import lru_cache
from typing import List, Tuple

import numpy
from tqdm import tqdm

from facefusion import inference_manager, state_manager, wording
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.face_helper import apply_nms
from facefusion.filesystem import resolve_relative_path
from facefusion.thread_helper import conditional_thread_semaphore
from facefusion.typing import BoundingBox, DownloadScope, Fps, InferencePool, ModelOptions, ModelSet, Score, VisionFrame
from facefusion.vision import detect_video_fps, get_video_frame, read_image, resize_frame_resolution

STREAM_COUNTER = 0


@lru_cache(maxsize = None)
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
	return\
	{
		'yolo_nsfw':
		{
			'hashes':
			{
				'content_analyser':
				{
					'url': resolve_download_url('models-3.2.0', 'yolo_11m_nsfw.hash'),
					'path': resolve_relative_path('../.assets/models/yolo_11m_nsfw.hash')
				}
			},
			'sources':
			{
				'content_analyser':
				{
					'url': resolve_download_url('models-3.2.0', 'yolo_11m_nsfw.onnx'),
					'path': resolve_relative_path('../.assets/models/yolo_11m_nsfw.onnx')
				}
			},
			'size': (640, 640)
		}
	}


def get_inference_pool() -> InferencePool:
	model_sources = get_model_options().get('sources')
	return inference_manager.get_inference_pool(__name__, model_sources)


def clear_inference_pool() -> None:
	inference_manager.clear_inference_pool(__name__)


def get_model_options() -> ModelOptions:
	return create_static_model_set('full').get('yolo_nsfw')


def pre_check() -> bool:
	model_hashes = get_model_options().get('hashes')
	model_sources = get_model_options().get('sources')

	return conditional_download_hashes(model_hashes) and conditional_download_sources(model_sources)


def analyse_stream(vision_frame : VisionFrame, video_fps : Fps) -> bool:
	global STREAM_COUNTER

	STREAM_COUNTER = STREAM_COUNTER + 1
	if STREAM_COUNTER % int(video_fps) == 0:
		return analyse_frame(vision_frame)
	return False


def analyse_frame(vision_frame : VisionFrame) -> bool:
	bounding_boxes, nsfw_scores = detect_nsfw(vision_frame)
	keep_indices = apply_nms(bounding_boxes, nsfw_scores, 0.2, 0.6)

	return len(keep_indices) > 0


@lru_cache(maxsize = None)
def analyse_image(image_path : str) -> bool:
	vision_frame = read_image(image_path)
	return analyse_frame(vision_frame)


@lru_cache(maxsize = None)
def analyse_video(video_path : str, trim_frame_start : int, trim_frame_end : int) -> bool:
	video_fps = detect_video_fps(video_path)
	frame_range = range(trim_frame_start, trim_frame_end)
	rate = 0.0
	counter = 0

	with tqdm(total = len(frame_range), desc = wording.get('analysing'), unit = 'frame', ascii = ' =', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:

		for frame_number in frame_range:
			if frame_number % int(video_fps) == 0:
				vision_frame = get_video_frame(video_path, frame_number)
				if analyse_frame(vision_frame):
					counter += 1
			rate = counter * int(video_fps) / len(frame_range) * 100
			progress.set_postfix(rate = rate)
			progress.update()

	return rate > 10.0


def detect_nsfw(vision_frame : VisionFrame) -> Tuple[List[BoundingBox], List[Score]]:
	bounding_boxes = []
	nsfw_scores = []
	model_size = get_model_options().get('size')
	temp_vision_frame = resize_frame_resolution(vision_frame, model_size)
	ratio_height = vision_frame.shape[0] / temp_vision_frame.shape[0]
	ratio_width = vision_frame.shape[1] / temp_vision_frame.shape[1]
	detect_vision_frame = prepare_detect_frame(temp_vision_frame)
	detection = forward(detect_vision_frame)
	detection = numpy.squeeze(detection).T
	bounding_boxes_raw = detection[:, :4]
	nsfw_scores_raw = numpy.amax(detection[:, 4:], axis = 1)
	keep_indices = numpy.where(nsfw_scores_raw > 0.2)[0]

	if numpy.any(keep_indices):
		bounding_boxes_raw, nsfw_scores_raw = bounding_boxes_raw[keep_indices], nsfw_scores_raw[keep_indices]

		for bounding_box_raw in bounding_boxes_raw:
			bounding_boxes.append(numpy.array(
			[
				(bounding_box_raw[0] - bounding_box_raw[2] / 2) * ratio_width,
				(bounding_box_raw[1] - bounding_box_raw[3] / 2) * ratio_height,
				(bounding_box_raw[0] + bounding_box_raw[2] / 2) * ratio_width,
				(bounding_box_raw[1] + bounding_box_raw[3] / 2) * ratio_height
			]))

		nsfw_scores = nsfw_scores_raw.ravel().tolist()

	return bounding_boxes, nsfw_scores


def forward(vision_frame : VisionFrame) -> float:
	content_analyser = get_inference_pool().get('content_analyser')

	with conditional_thread_semaphore():
		detection = content_analyser.run(None,
		{
			'input': vision_frame
		})

	return detection


def prepare_detect_frame(temp_vision_frame : VisionFrame) -> VisionFrame:
	model_size = get_model_options().get('size')
	detect_vision_frame = numpy.zeros((model_size[0], model_size[1], 3))
	detect_vision_frame[:temp_vision_frame.shape[0], :temp_vision_frame.shape[1], :] = temp_vision_frame
	detect_vision_frame = detect_vision_frame / 255.0
	detect_vision_frame = numpy.expand_dims(detect_vision_frame.transpose(2, 0, 1), axis = 0).astype(numpy.float32)
	return detect_vision_frame
