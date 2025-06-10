from functools import lru_cache
from typing import Tuple

import numpy
from tqdm import tqdm

from facefusion import inference_manager, state_manager, wording
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.filesystem import resolve_relative_path
from facefusion.thread_helper import conditional_thread_semaphore
from facefusion.types import Detection, DownloadScope, DownloadSet, Fps, InferencePool, ModelSet, VisionFrame
from facefusion.vision import detect_video_fps, fit_frame, read_image, read_video_frame

STREAM_COUNTER = 0


@lru_cache(maxsize = None)
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
	return\
	{
		'yolo_11m':
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
			'threshold': 0.2,
			'size': (640, 640),
			'mean': (0.0, 0.0, 0.0),
			'standard_deviation': (1.0, 1.0, 1.0)
		},
		'marqo':
		{
			'hashes':
			{
				'content_analyser':
				{
					'url': 'https://huggingface.co/bluefoxcreation/Models/resolve/main/nsfw_detectors/marqo_nsfw.hash',
					'path': resolve_relative_path('../.assets/models/marqo_nsfw.hash')
				}
			},
			'sources':
			{
				'content_analyser':
				{
					'url': 'https://huggingface.co/bluefoxcreation/Models/resolve/main/nsfw_detectors/marqo_nsfw.onnx',
					'path': resolve_relative_path('../.assets/models/marqo_nsfw.onnx')
				}
			},
			'threshold': 0.24,
			'size': (384, 384),
			'mean': (0.5, 0.5, 0.5),
			'standard_deviation': (0.5, 0.5, 0.5)
		},
		'freepik':
		{
			'hashes':
			{
				'content_analyser':
				{
					'url': 'https://huggingface.co/bluefoxcreation/Models/resolve/main/nsfw_detectors/freepik_nsfw.hash',
					'path': resolve_relative_path('../.assets/models/freepik_nsfw.hash')
				}
			},
			'sources':
			{
				'content_analyser':
				{
					'url': 'https://huggingface.co/bluefoxcreation/Models/resolve/main/nsfw_detectors/freepik_nsfw.onnx',
					'path': resolve_relative_path('../.assets/models/freepik_nsfw.onnx')
				}
			},
			'threshold': 10.5,
			'size': (448, 448),
			'mean': (0.48145466, 0.4578275, 0.40821073),
			'standard_deviation': (0.26862954, 0.26130258, 0.27577711)
		}
	}


def get_inference_pool() -> InferencePool:
	model_names = [ 'yolo_11m', 'marqo', 'freepik' ]
	_, model_source_set = collect_model_downloads()

	return inference_manager.get_inference_pool(__name__, model_names, model_source_set)


def clear_inference_pool() -> None:
	model_names = [ 'yolo_11m', 'marqo', 'freepik' ]
	inference_manager.clear_inference_pool(__name__, model_names)


def collect_model_downloads() -> Tuple[DownloadSet, DownloadSet]:
	model_set = create_static_model_set('full')
	model_hash_set = {}
	model_source_set = {}

	for nsfw_model in [ 'yolo_11m', 'marqo', 'freepik' ]:
		model_hash_set[nsfw_model] = model_set.get(nsfw_model).get('hashes').get('content_analyser')
		model_source_set[nsfw_model] = model_set.get(nsfw_model).get('sources').get('content_analyser')

	return model_hash_set, model_source_set


def pre_check() -> bool:
	model_hash_set, model_source_set = collect_model_downloads()

	return conditional_download_hashes(model_hash_set) and conditional_download_sources(model_source_set)


def analyse_stream(vision_frame : VisionFrame, video_fps : Fps) -> bool:
	global STREAM_COUNTER

	STREAM_COUNTER = STREAM_COUNTER + 1
	if STREAM_COUNTER % int(video_fps) == 0:
		return analyse_frame(vision_frame)
	return False


def analyse_frame(vision_frame : VisionFrame) -> bool:
	return detect_nsfw(vision_frame)


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


def detect_nsfw(vision_frame : VisionFrame) -> bool:

	if detect_with_yolo_11m(vision_frame):

		if detect_with_marqo(vision_frame):
			return True

		return detect_with_freepik(vision_frame)
	return False


def detect_with_yolo_11m(vision_frame : VisionFrame) -> bool:
	model_name = 'yolo_11m'
	model_set = create_static_model_set('full').get(model_name)
	model_threshold = model_set.get('threshold')

	detect_vision_frame = prepare_detect_frame(vision_frame, model_name)
	detection = forward_yolo_11m(detect_vision_frame)
	detection_score = numpy.max(numpy.amax(detection[:, 4:], axis = 1))
	return detection_score > model_threshold


def detect_with_marqo(vision_frame : VisionFrame) -> bool:
	model_name = 'marqo'
	model_set = create_static_model_set('full').get(model_name)
	model_threshold = model_set.get('threshold')

	detect_vision_frame = prepare_detect_frame(vision_frame, model_name)
	detection = forward_marqo(detect_vision_frame)[0]
	detection_score = detection[0] - detection[1]
	return detection_score > model_threshold


def detect_with_freepik(vision_frame : VisionFrame) -> bool:
	model_name = 'freepik'
	model_set = create_static_model_set('full').get(model_name)
	model_threshold = model_set.get('threshold')

	detect_vision_frame = prepare_detect_frame(vision_frame, model_name)
	detection = forward_freepik(detect_vision_frame)[0]
	detection_score = (detection[2] + detection[3]) - (detection[0] + detection[1])
	return detection_score > model_threshold


def forward_yolo_11m(vision_frame : VisionFrame) -> Detection:
	content_analyser = get_inference_pool().get('yolo_11m')

	with conditional_thread_semaphore():
		detection = content_analyser.run(None,
		{
			'input': vision_frame
		})[0]

	return detection


def forward_marqo(vision_frame : VisionFrame) -> Detection:
	content_analyser = get_inference_pool().get('marqo')

	with conditional_thread_semaphore():
		detection = content_analyser.run(None,
		{
			'input': vision_frame
		})[0]

	return detection


def forward_freepik(vision_frame : VisionFrame) -> Detection:
	content_analyser = get_inference_pool().get('freepik')

	with conditional_thread_semaphore():
		detection = content_analyser.run(None,
		{
			'input': vision_frame
		})[0]

	return detection


def prepare_detect_frame(temp_vision_frame : VisionFrame, model_name : str) -> VisionFrame:
	model_set = create_static_model_set('full').get(model_name)
	model_size = model_set.get('size')
	model_mean = model_set.get('mean')
	model_standard_deviation = model_set.get('standard_deviation')

	detect_vision_frame = fit_frame(temp_vision_frame, model_size)
	detect_vision_frame = detect_vision_frame[:, :, ::-1] / 255.0
	detect_vision_frame -= model_mean
	detect_vision_frame /= model_standard_deviation
	detect_vision_frame = numpy.expand_dims(detect_vision_frame.transpose(2, 0, 1), axis = 0).astype(numpy.float32)
	return detect_vision_frame
