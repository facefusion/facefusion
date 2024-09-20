from functools import lru_cache

import cv2
import numpy
from tqdm import tqdm

from facefusion import inference_manager, state_manager, wording
from facefusion.download import conditional_download_hashes, conditional_download_sources
from facefusion.filesystem import resolve_relative_path
from facefusion.thread_helper import conditional_thread_semaphore
from facefusion.typing import Fps, InferencePool, ModelOptions, ModelSet, VisionFrame
from facefusion.vision import count_video_frame_total, detect_video_fps, get_video_frame, read_image

MODEL_SET : ModelSet =\
{
	'open_nsfw':
	{
		'hashes':
		{
			'content_analyser':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/open_nsfw.hash',
				'path': resolve_relative_path('../.assets/models/open_nsfw.hash')
			}
		},
		'sources':
		{
			'content_analyser':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/open_nsfw.onnx',
				'path': resolve_relative_path('../.assets/models/open_nsfw.onnx')
			}
		},
		'size': (224, 224),
		'mean': [ 104, 117, 123 ]
	}
}
PROBABILITY_LIMIT = 0.80
RATE_LIMIT = 10
STREAM_COUNTER = 0


def get_inference_pool() -> InferencePool:
	model_sources = get_model_options().get('sources')
	return inference_manager.get_inference_pool(__name__, model_sources)


def clear_inference_pool() -> None:
	inference_manager.clear_inference_pool(__name__)


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
	vision_frame = prepare_frame(vision_frame)
	probability = forward(vision_frame)

	return probability > PROBABILITY_LIMIT


def forward(vision_frame : VisionFrame) -> float:
	content_analyser = get_inference_pool().get('content_analyser')

	with conditional_thread_semaphore():
		probability = content_analyser.run(None,
		{
			'input': vision_frame
		})[0][0][1]

	return probability


def prepare_frame(vision_frame : VisionFrame) -> VisionFrame:
	model_size = get_model_options().get('size')
	model_mean = get_model_options().get('mean')
	vision_frame = cv2.resize(vision_frame, model_size).astype(numpy.float32)
	vision_frame -= numpy.array(model_mean).astype(numpy.float32)
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
