from functools import lru_cache
from time import sleep
from typing import Optional

import cv2
import numpy
from tqdm import tqdm

from facefusion import process_manager, state_manager, wording
from facefusion.execution import create_inference_pool
from facefusion.filesystem import resolve_relative_path
from facefusion.source_helper import conditional_download_hashes, conditional_download_sources
from facefusion.thread_helper import conditional_thread_semaphore, thread_lock
from facefusion.typing import Fps, InferencePool, ModelOptions, ModelSet, VisionFrame
from facefusion.vision import count_video_frame_total, detect_video_fps, get_video_frame, read_image

INFERENCE_POOL : Optional[InferencePool] = None
MODEL_SET : ModelSet =\
{
	'open_nsfw':
	{
		'hashes':
		{
			'content_analyser':
			{
				'url': 'https://huggingface.co/facefusion/hashes/raw/main/open_nsfw.hash',
				'path': resolve_relative_path('../.assets/models/open_nsfw.hash')
			}
		},
		'sources':
		{
			'content_analyser':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/open_nsfw.onnx',
				'path': resolve_relative_path('../.assets/models/open_nsfw.onnx')
			}
		}
	}
}
PROBABILITY_LIMIT = 0.80
RATE_LIMIT = 10
STREAM_COUNTER = 0


def get_inference_pool() -> InferencePool:
	global INFERENCE_POOL

	with thread_lock():
		while process_manager.is_checking():
			sleep(0.5)
		if INFERENCE_POOL is None:
			model_sources = get_model_options().get('sources')
			INFERENCE_POOL = create_inference_pool(model_sources, state_manager.get_item('execution_device_id'), state_manager.get_item('execution_providers'))
		return INFERENCE_POOL


def clear_inference_pool() -> None:
	global INFERENCE_POOL

	INFERENCE_POOL = None


def get_model_options() -> ModelOptions:
	return MODEL_SET.get('open_nsfw')


def pre_check() -> bool:
	download_directory_path = resolve_relative_path('../.assets/models')
	model_hashes = get_model_options().get('hashes')
	model_sources = get_model_options().get('sources')

	return conditional_download_hashes(download_directory_path, model_hashes) and conditional_download_sources(download_directory_path, model_sources)


def analyse_stream(vision_frame : VisionFrame, video_fps : Fps) -> bool:
	global STREAM_COUNTER

	STREAM_COUNTER = STREAM_COUNTER + 1
	if STREAM_COUNTER % int(video_fps) == 0:
		return analyse_frame(vision_frame)
	return False


def analyse_frame(vision_frame : VisionFrame) -> bool:
	content_analyser = get_inference_pool().get('content_analyser')
	vision_frame = prepare_frame(vision_frame)

	with conditional_thread_semaphore():
		probability = content_analyser.run(None,
		{
			content_analyser.get_inputs()[0].name: vision_frame
		})[0][0][1]

	return probability > PROBABILITY_LIMIT


def prepare_frame(vision_frame : VisionFrame) -> VisionFrame:
	vision_frame = cv2.resize(vision_frame, (224, 224)).astype(numpy.float32)
	vision_frame -= numpy.array([ 104, 117, 123 ]).astype(numpy.float32)
	vision_frame = numpy.expand_dims(vision_frame, axis = 0)
	return vision_frame


@lru_cache(maxsize = None)
def analyse_image(image_path : str) -> bool:
	frame = read_image(image_path)
	return analyse_frame(frame)


@lru_cache(maxsize = None)
def analyse_video(video_path : str, start_frame : int, end_frame : int) -> bool:
	video_frame_total = count_video_frame_total(video_path)
	video_fps = detect_video_fps(video_path)
	frame_range = range(start_frame or 0, end_frame or video_frame_total)
	rate = 0.0
	counter = 0

	with tqdm(total = len(frame_range), desc = wording.get('analysing'), unit = 'frame', ascii = ' =', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
		for frame_number in frame_range:
			if frame_number % int(video_fps) == 0:
				frame = get_video_frame(video_path, frame_number)
				if analyse_frame(frame):
					counter += 1
			rate = counter * int(video_fps) / len(frame_range) * 100
			progress.update()
			progress.set_postfix(rate = rate)
	return rate > RATE_LIMIT
