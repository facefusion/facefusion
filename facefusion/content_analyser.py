from functools import lru_cache
from typing import List

import numpy
from tqdm import tqdm

from facefusion import inference_manager, state_manager, wording
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.filesystem import resolve_relative_path
from facefusion.thread_helper import conditional_thread_semaphore
from facefusion.types import Detection, DownloadScope, Fps, InferencePool, ModelOptions, ModelSet, Score, VisionFrame
from facefusion.vision import detect_video_fps, fit_frame, read_image, read_video_frame

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
	model_names = [ 'yolo_nsfw' ]
	model_source_set = get_model_options().get('sources')

	return inference_manager.get_inference_pool(__name__, model_names, model_source_set)


def clear_inference_pool() -> None:
	model_names = [ 'yolo_nsfw' ]
	inference_manager.clear_inference_pool(__name__, model_names)


def get_model_options() -> ModelOptions:
	return create_static_model_set('full').get('yolo_nsfw')


def pre_check() -> bool:
	model_hash_set = get_model_options().get('hashes')
	model_source_set = get_model_options().get('sources')

	return conditional_download_hashes(model_hash_set) and conditional_download_sources(model_source_set)


def analyse_stream(vision_frame : VisionFrame, video_fps : Fps) -> bool:
	global STREAM_COUNTER

	STREAM_COUNTER = STREAM_COUNTER + 1
	if STREAM_COUNTER % int(video_fps) == 0:
		return analyse_frame(vision_frame)
	return False


def analyse_frame(vision_frame : VisionFrame) -> bool:
	nsfw_scores = detect_nsfw(vision_frame)

	return len(nsfw_scores) > 0


@lru_cache(maxsize = None)
def analyse_image(image_path : str) -> bool:
	vision_frame = read_image(image_path)
	return analyse_frame(vision_frame)


@lru_cache(maxsize = None)
def analyse_video(video_path : str, trim_frame_start : int, trim_frame_end : int) -> bool:
	video_fps = detect_video_fps(video_path)
	frame_range = range(trim_frame_start, trim_frame_end)
	rate = 0.0
	total = 0
	counter = 0

	with tqdm(total = len(frame_range), desc = wording.get('analysing'), unit = 'frame', ascii = ' =', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:

		for frame_number in frame_range:
			if frame_number % int(video_fps) == 0:
				vision_frame = read_video_frame(video_path, frame_number)
				total += 1
				if analyse_frame(vision_frame):
					counter += 1
			if counter > 0 and total > 0:
				rate = counter / total * 100
			progress.set_postfix(rate = rate)
			progress.update()

	return rate > 10.0


def detect_nsfw(vision_frame : VisionFrame) -> List[Score]:
	nsfw_scores = []
	model_size = get_model_options().get('size')
	temp_vision_frame = fit_frame(vision_frame, model_size)
	detect_vision_frame = prepare_detect_frame(temp_vision_frame)
	detection = forward(detect_vision_frame)
	detection = numpy.squeeze(detection).T
	nsfw_scores_raw = numpy.amax(detection[:, 4:], axis = 1)
	keep_indices = numpy.where(nsfw_scores_raw > 0.2)[0]

	if numpy.any(keep_indices):
		nsfw_scores_raw = nsfw_scores_raw[keep_indices]
		nsfw_scores = nsfw_scores_raw.ravel().tolist()

	return nsfw_scores


def forward(vision_frame : VisionFrame) -> Detection:
	content_analyser = get_inference_pool().get('content_analyser')

	with conditional_thread_semaphore():
		detection = content_analyser.run(None,
		{
			'input': vision_frame
		})

	return detection


def prepare_detect_frame(temp_vision_frame : VisionFrame) -> VisionFrame:
	detect_vision_frame = temp_vision_frame / 255.0
	detect_vision_frame = numpy.expand_dims(detect_vision_frame.transpose(2, 0, 1), axis = 0).astype(numpy.float32)
	return detect_vision_frame
