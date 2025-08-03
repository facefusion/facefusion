from functools import lru_cache
from typing import List, Tuple

import numpy
from tqdm import tqdm

from facefusion import inference_manager, state_manager, wording
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.execution import has_execution_provider
from facefusion.filesystem import resolve_relative_path
from facefusion.thread_helper import conditional_thread_semaphore
from facefusion.types import Detection, DownloadScope, DownloadSet, ExecutionProvider, Fps, InferencePool, ModelSet, VisionFrame
from facefusion.vision import detect_video_fps, fit_frame, read_image, read_video_frame

STREAM_COUNTER = 0


@lru_cache(maxsize = None)
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
	return\
	{
		'nsfw_1':
		{
			'hashes':
			{
				'content_analyser':
				{
					'url': resolve_download_url('models-3.3.0', 'nsfw_1.hash'),
					'path': resolve_relative_path('../.assets/models/nsfw_1.hash')
				}
			},
			'sources':
			{
				'content_analyser':
				{
					'url': resolve_download_url('models-3.3.0', 'nsfw_1.onnx'),
					'path': resolve_relative_path('../.assets/models/nsfw_1.onnx')
				}
			},
			'size': (640, 640),
			'mean': (0.0, 0.0, 0.0),
			'standard_deviation': (1.0, 1.0, 1.0)
		},
		'nsfw_2':
		{
			'hashes':
			{
				'content_analyser':
				{
					'url': resolve_download_url('models-3.3.0', 'nsfw_2.hash'),
					'path': resolve_relative_path('../.assets/models/nsfw_2.hash')
				}
			},
			'sources':
			{
				'content_analyser':
				{
					'url': resolve_download_url('models-3.3.0', 'nsfw_2.onnx'),
					'path': resolve_relative_path('../.assets/models/nsfw_2.onnx')
				}
			},
			'size': (384, 384),
			'mean': (0.5, 0.5, 0.5),
			'standard_deviation': (0.5, 0.5, 0.5)
		},
		'nsfw_3':
		{
			'hashes':
			{
				'content_analyser':
				{
					'url': resolve_download_url('models-3.3.0', 'nsfw_3.hash'),
					'path': resolve_relative_path('../.assets/models/nsfw_3.hash')
				}
			},
			'sources':
			{
				'content_analyser':
				{
					'url': resolve_download_url('models-3.3.0', 'nsfw_3.onnx'),
					'path': resolve_relative_path('../.assets/models/nsfw_3.onnx')
				}
			},
			'size': (448, 448),
			'mean': (0.48145466, 0.4578275, 0.40821073),
			'standard_deviation': (0.26862954, 0.26130258, 0.27577711)
		}
	}


def get_inference_pool() -> InferencePool:
	model_names = [ 'nsfw_1', 'nsfw_2', 'nsfw_3' ]
	_, model_source_set = collect_model_downloads()

	return inference_manager.get_inference_pool(__name__, model_names, model_source_set)


def clear_inference_pool() -> None:
	model_names = [ 'nsfw_1', 'nsfw_2', 'nsfw_3' ]
	inference_manager.clear_inference_pool(__name__, model_names)


def resolve_execution_providers() -> List[ExecutionProvider]:
	if has_execution_provider('coreml'):
		return [ 'cpu' ]
	return state_manager.get_item('execution_providers')


def collect_model_downloads() -> Tuple[DownloadSet, DownloadSet]:
	model_set = create_static_model_set('full')
	model_hash_set = {}
	model_source_set = {}

	for content_analyser_model in [ 'nsfw_1', 'nsfw_2', 'nsfw_3' ]:
		model_hash_set[content_analyser_model] = model_set.get(content_analyser_model).get('hashes').get('content_analyser')
		model_source_set[content_analyser_model] = model_set.get(content_analyser_model).get('sources').get('content_analyser')

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
	return False


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

	return bool(rate > 10.0)


def detect_nsfw(vision_frame : VisionFrame) -> bool:
	is_nsfw_1 = detect_with_nsfw_1(vision_frame)
	is_nsfw_2 = detect_with_nsfw_2(vision_frame)
	is_nsfw_3 = detect_with_nsfw_3(vision_frame)

	return is_nsfw_1 and is_nsfw_2 or is_nsfw_1 and is_nsfw_3 or is_nsfw_2 and is_nsfw_3


def detect_with_nsfw_1(vision_frame : VisionFrame) -> bool:
	detect_vision_frame = prepare_detect_frame(vision_frame, 'nsfw_1')
	detection = forward_nsfw(detect_vision_frame, 'nsfw_1')
	detection_score = numpy.max(numpy.amax(detection[:, 4:], axis = 1))
	return bool(detection_score > 0.2)


def detect_with_nsfw_2(vision_frame : VisionFrame) -> bool:
	detect_vision_frame = prepare_detect_frame(vision_frame, 'nsfw_2')
	detection = forward_nsfw(detect_vision_frame, 'nsfw_2')
	detection_score = detection[0] - detection[1]
	return bool(detection_score > 0.25)


def detect_with_nsfw_3(vision_frame : VisionFrame) -> bool:
	detect_vision_frame = prepare_detect_frame(vision_frame, 'nsfw_3')
	detection = forward_nsfw(detect_vision_frame, 'nsfw_3')
	detection_score = (detection[2] + detection[3]) - (detection[0] + detection[1])
	return bool(detection_score > 10.5)


def forward_nsfw(vision_frame : VisionFrame, nsfw_model : str) -> Detection:
	content_analyser = get_inference_pool().get(nsfw_model)

	with conditional_thread_semaphore():
		detection = content_analyser.run(None,
		{
			'input': vision_frame
		})[0]

	if nsfw_model in [ 'nsfw_2', 'nsfw_3' ]:
		return detection[0]

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
