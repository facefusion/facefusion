from argparse import ArgumentParser
from functools import lru_cache
from typing import List

import cv2
import numpy

import facefusion.jobs.job_manager
import facefusion.jobs.job_store
import facefusion.processors.core as processors
from facefusion import config, content_analyser, inference_manager, logger, process_manager, state_manager, video_manager, wording
from facefusion.common_helper import create_int_metavar
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.execution import has_execution_provider
from facefusion.filesystem import in_directory, is_image, is_video, resolve_relative_path, same_file_extension
from facefusion.processors import choices as processors_choices
from facefusion.processors.types import FrameColorizerInputs
from facefusion.program_helper import find_argument_group
from facefusion.thread_helper import thread_semaphore
from facefusion.types import ApplyStateItem, Args, DownloadScope, ExecutionProvider, Face, InferencePool, ModelOptions, ModelSet, ProcessMode, QueuePayload, UpdateProgress, VisionFrame
from facefusion.vision import read_image, read_static_image, unpack_resolution, write_image


@lru_cache(maxsize = None)
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
	return\
	{
		'ddcolor':
		{
			'hashes':
			{
				'frame_colorizer':
				{
					'url': resolve_download_url('models-3.0.0', 'ddcolor.hash'),
					'path': resolve_relative_path('../.assets/models/ddcolor.hash')
				}
			},
			'sources':
			{
				'frame_colorizer':
				{
					'url': resolve_download_url('models-3.0.0', 'ddcolor.onnx'),
					'path': resolve_relative_path('../.assets/models/ddcolor.onnx')
				}
			},
			'type': 'ddcolor'
		},
		'ddcolor_artistic':
		{
			'hashes':
			{
				'frame_colorizer':
				{
					'url': resolve_download_url('models-3.0.0', 'ddcolor_artistic.hash'),
					'path': resolve_relative_path('../.assets/models/ddcolor_artistic.hash')
				}
			},
			'sources':
			{
				'frame_colorizer':
				{
					'url': resolve_download_url('models-3.0.0', 'ddcolor_artistic.onnx'),
					'path': resolve_relative_path('../.assets/models/ddcolor_artistic.onnx')
				}
			},
			'type': 'ddcolor'
		},
		'deoldify':
		{
			'hashes':
			{
				'frame_colorizer':
				{
					'url': resolve_download_url('models-3.0.0', 'deoldify.hash'),
					'path': resolve_relative_path('../.assets/models/deoldify.hash')
				}
			},
			'sources':
			{
				'frame_colorizer':
				{
					'url': resolve_download_url('models-3.0.0', 'deoldify.onnx'),
					'path': resolve_relative_path('../.assets/models/deoldify.onnx')
				}
			},
			'type': 'deoldify'
		},
		'deoldify_artistic':
		{
			'hashes':
			{
				'frame_colorizer':
				{
					'url': resolve_download_url('models-3.0.0', 'deoldify_artistic.hash'),
					'path': resolve_relative_path('../.assets/models/deoldify_artistic.hash')
				}
			},
			'sources':
			{
				'frame_colorizer':
				{
					'url': resolve_download_url('models-3.0.0', 'deoldify_artistic.onnx'),
					'path': resolve_relative_path('../.assets/models/deoldify_artistic.onnx')
				}
			},
			'type': 'deoldify'
		},
		'deoldify_stable':
		{
			'hashes':
			{
				'frame_colorizer':
				{
					'url': resolve_download_url('models-3.0.0', 'deoldify_stable.hash'),
					'path': resolve_relative_path('../.assets/models/deoldify_stable.hash')
				}
			},
			'sources':
			{
				'frame_colorizer':
				{
					'url': resolve_download_url('models-3.0.0', 'deoldify_stable.onnx'),
					'path': resolve_relative_path('../.assets/models/deoldify_stable.onnx')
				}
			},
			'type': 'deoldify'
		}
	}


def get_inference_pool() -> InferencePool:
	model_names = [ state_manager.get_item('frame_colorizer_model') ]
	model_source_set = get_model_options().get('sources')

	return inference_manager.get_inference_pool(__name__, model_names, model_source_set)


def clear_inference_pool() -> None:
	model_names = [ state_manager.get_item('frame_colorizer_model') ]
	inference_manager.clear_inference_pool(__name__, model_names)


def resolve_execution_providers() -> List[ExecutionProvider]:
	if has_execution_provider('coreml'):
		return [ 'cpu' ]
	return state_manager.get_item('execution_providers')


def get_model_options() -> ModelOptions:
	model_name = state_manager.get_item('frame_colorizer_model')
	return create_static_model_set('full').get(model_name)


def register_args(program : ArgumentParser) -> None:
	group_processors = find_argument_group(program, 'processors')
	if group_processors:
		group_processors.add_argument('--frame-colorizer-model', help = wording.get('help.frame_colorizer_model'), default = config.get_str_value('processors', 'frame_colorizer_model', 'ddcolor'), choices = processors_choices.frame_colorizer_models)
		group_processors.add_argument('--frame-colorizer-size', help = wording.get('help.frame_colorizer_size'), type = str, default = config.get_str_value('processors', 'frame_colorizer_size', '256x256'), choices = processors_choices.frame_colorizer_sizes)
		group_processors.add_argument('--frame-colorizer-blend', help = wording.get('help.frame_colorizer_blend'), type = int, default = config.get_int_value('processors', 'frame_colorizer_blend', '100'), choices = processors_choices.frame_colorizer_blend_range, metavar = create_int_metavar(processors_choices.frame_colorizer_blend_range))
		facefusion.jobs.job_store.register_step_keys([ 'frame_colorizer_model', 'frame_colorizer_blend', 'frame_colorizer_size' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('frame_colorizer_model', args.get('frame_colorizer_model'))
	apply_state_item('frame_colorizer_blend', args.get('frame_colorizer_blend'))
	apply_state_item('frame_colorizer_size', args.get('frame_colorizer_size'))


def pre_check() -> bool:
	model_hash_set = get_model_options().get('hashes')
	model_source_set = get_model_options().get('sources')

	return conditional_download_hashes(model_hash_set) and conditional_download_sources(model_source_set)


def pre_process(mode : ProcessMode) -> bool:
	if mode in [ 'output', 'preview' ] and not is_image(state_manager.get_item('target_path')) and not is_video(state_manager.get_item('target_path')):
		logger.error(wording.get('choose_image_or_video_target') + wording.get('exclamation_mark'), __name__)
		return False
	if mode == 'output' and not in_directory(state_manager.get_item('output_path')):
		logger.error(wording.get('specify_image_or_video_output') + wording.get('exclamation_mark'), __name__)
		return False
	if mode == 'output' and not same_file_extension(state_manager.get_item('target_path'), state_manager.get_item('output_path')):
		logger.error(wording.get('match_target_and_output_extension') + wording.get('exclamation_mark'), __name__)
		return False
	return True


def post_process() -> None:
	read_static_image.cache_clear()
	video_manager.clear_video_pool()
	if state_manager.get_item('video_memory_strategy') in [ 'strict', 'moderate' ]:
		clear_inference_pool()
	if state_manager.get_item('video_memory_strategy') == 'strict':
		content_analyser.clear_inference_pool()


def colorize_frame(temp_vision_frame : VisionFrame) -> VisionFrame:
	color_vision_frame = prepare_temp_frame(temp_vision_frame)
	color_vision_frame = forward(color_vision_frame)
	color_vision_frame = merge_color_frame(temp_vision_frame, color_vision_frame)
	color_vision_frame = blend_frame(temp_vision_frame, color_vision_frame)
	return color_vision_frame


def forward(color_vision_frame : VisionFrame) -> VisionFrame:
	frame_colorizer = get_inference_pool().get('frame_colorizer')

	with thread_semaphore():
		color_vision_frame = frame_colorizer.run(None,
		{
			'input': color_vision_frame
		})[0][0]

	return color_vision_frame


def prepare_temp_frame(temp_vision_frame : VisionFrame) -> VisionFrame:
	model_size = unpack_resolution(state_manager.get_item('frame_colorizer_size'))
	model_type = get_model_options().get('type')
	temp_vision_frame = cv2.cvtColor(temp_vision_frame, cv2.COLOR_BGR2GRAY)
	temp_vision_frame = cv2.cvtColor(temp_vision_frame, cv2.COLOR_GRAY2RGB)

	if model_type == 'ddcolor':
		temp_vision_frame = (temp_vision_frame / 255.0).astype(numpy.float32) #type:ignore[operator]
		temp_vision_frame = cv2.cvtColor(temp_vision_frame, cv2.COLOR_RGB2LAB)[:, :, :1]
		temp_vision_frame = numpy.concatenate((temp_vision_frame, numpy.zeros_like(temp_vision_frame), numpy.zeros_like(temp_vision_frame)), axis = -1)
		temp_vision_frame = cv2.cvtColor(temp_vision_frame, cv2.COLOR_LAB2RGB)

	temp_vision_frame = cv2.resize(temp_vision_frame, model_size)
	temp_vision_frame = temp_vision_frame.transpose((2, 0, 1))
	temp_vision_frame = numpy.expand_dims(temp_vision_frame, axis = 0).astype(numpy.float32)
	return temp_vision_frame


def merge_color_frame(temp_vision_frame : VisionFrame, color_vision_frame : VisionFrame) -> VisionFrame:
	model_type = get_model_options().get('type')
	color_vision_frame = color_vision_frame.transpose(1, 2, 0)
	color_vision_frame = cv2.resize(color_vision_frame, (temp_vision_frame.shape[1], temp_vision_frame.shape[0]))

	if model_type == 'ddcolor':
		temp_vision_frame = (temp_vision_frame / 255.0).astype(numpy.float32)
		temp_vision_frame = cv2.cvtColor(temp_vision_frame, cv2.COLOR_BGR2LAB)[:, :, :1]
		color_vision_frame = numpy.concatenate((temp_vision_frame, color_vision_frame), axis = -1)
		color_vision_frame = cv2.cvtColor(color_vision_frame, cv2.COLOR_LAB2BGR)
		color_vision_frame = (color_vision_frame * 255.0).round().astype(numpy.uint8) #type:ignore[operator]

	if model_type == 'deoldify':
		temp_blue_channel, _, _ = cv2.split(temp_vision_frame)
		color_vision_frame = cv2.cvtColor(color_vision_frame, cv2.COLOR_BGR2RGB).astype(numpy.uint8)
		color_vision_frame = cv2.cvtColor(color_vision_frame, cv2.COLOR_BGR2LAB)
		_, color_green_channel, color_red_channel = cv2.split(color_vision_frame)
		color_vision_frame = cv2.merge((temp_blue_channel, color_green_channel, color_red_channel))
		color_vision_frame = cv2.cvtColor(color_vision_frame, cv2.COLOR_LAB2BGR)
	return color_vision_frame


def blend_frame(temp_vision_frame : VisionFrame, paste_vision_frame : VisionFrame) -> VisionFrame:
	frame_colorizer_blend = 1 - (state_manager.get_item('frame_colorizer_blend') / 100)
	temp_vision_frame = cv2.addWeighted(temp_vision_frame, frame_colorizer_blend, paste_vision_frame, 1 - frame_colorizer_blend, 0)
	return temp_vision_frame


def get_reference_frame(source_face : Face, target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	pass


def process_frame(inputs : FrameColorizerInputs) -> VisionFrame:
	target_vision_frame = inputs.get('target_vision_frame')
	return colorize_frame(target_vision_frame)


def process_frames(source_paths : List[str], queue_payloads : List[QueuePayload], update_progress : UpdateProgress) -> None:
	for queue_payload in process_manager.manage(queue_payloads):
		target_vision_path = queue_payload['frame_path']
		target_vision_frame = read_image(target_vision_path)
		output_vision_frame = process_frame(
		{
			'target_vision_frame': target_vision_frame
		})
		write_image(target_vision_path, output_vision_frame)
		update_progress(1)


def process_image(source_paths : List[str], target_path : str, output_path : str) -> None:
	target_vision_frame = read_static_image(target_path)
	output_vision_frame = process_frame(
	{
		'target_vision_frame': target_vision_frame
	})
	write_image(output_path, output_vision_frame)


def process_video(source_paths : List[str], temp_frame_paths : List[str]) -> None:
	processors.multi_process_frames(None, temp_frame_paths, process_frames)
