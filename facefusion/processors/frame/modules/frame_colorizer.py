from argparse import ArgumentParser
from time import sleep
from typing import Any, List, Literal, Optional

import cv2
import numpy
import onnxruntime

import facefusion.jobs.job_manager
import facefusion.jobs.job_store
import facefusion.processors.frame.core as frame_processors
from facefusion import config, logger, process_manager, state_manager, wording
from facefusion.common_helper import create_metavar
from facefusion.content_analyser import clear_content_analyser
from facefusion.download import conditional_download, is_download_done
from facefusion.execution import apply_execution_provider_options, has_execution_provider
from facefusion.face_analyser import clear_face_analyser
from facefusion.filesystem import in_directory, is_file, is_image, is_video, resolve_relative_path, same_file_extension
from facefusion.processors.frame import choices as frame_processors_choices
from facefusion.processors.frame.typing import FrameColorizerInputs
from facefusion.program_helper import find_argument_group
from facefusion.thread_helper import thread_lock, thread_semaphore
from facefusion.typing import Args, ExecutionProviderKey, Face, ModelSet, OptionsWithModel, ProcessMode, QueuePayload, \
	UpdateProgress, VisionFrame
from facefusion.vision import read_image, read_static_image, unpack_resolution, write_image

FRAME_PROCESSOR = None
NAME = __name__.upper()
MODELS : ModelSet =\
{
	'ddcolor':
	{
		'type': 'ddcolor',
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/ddcolor.onnx',
		'path': resolve_relative_path('../.assets/models/ddcolor.onnx')
	},
	'ddcolor_artistic':
	{
		'type': 'ddcolor',
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/ddcolor_artistic.onnx',
		'path': resolve_relative_path('../.assets/models/ddcolor_artistic.onnx')
	},
	'deoldify':
	{
		'type': 'deoldify',
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/deoldify.onnx',
		'path': resolve_relative_path('../.assets/models/deoldify.onnx')
	},
	'deoldify_artistic':
	{
		'type': 'deoldify',
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/deoldify_artistic.onnx',
		'path': resolve_relative_path('../.assets/models/deoldify_artistic.onnx')
	},
	'deoldify_stable':
	{
		'type': 'deoldify',
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/deoldify_stable.onnx',
		'path': resolve_relative_path('../.assets/models/deoldify_stable.onnx')
	}
}
OPTIONS : Optional[OptionsWithModel] = None


def get_frame_processor() -> Any:
	global FRAME_PROCESSOR

	with thread_lock():
		while process_manager.is_checking():
			sleep(0.5)
		if FRAME_PROCESSOR is None:
			model_path = get_options('model').get('path')
			execution_providers : List[ExecutionProviderKey] = [ 'cpu' ] if has_execution_provider('coreml') else state_manager.get_item('execution_providers')
			FRAME_PROCESSOR = onnxruntime.InferenceSession(model_path, providers = apply_execution_provider_options(state_manager.get_item('execution_device_id'), execution_providers))
	return FRAME_PROCESSOR


def clear_frame_processor() -> None:
	global FRAME_PROCESSOR

	FRAME_PROCESSOR = None


def get_options(key : Literal['model']) -> Any:
	global OPTIONS

	if OPTIONS is None:
		OPTIONS =\
		{
			'model': MODELS[state_manager.get_item('frame_colorizer_model')]
		}
	return OPTIONS.get(key)


def set_options(key : Literal['model'], value : Any) -> None:
	global OPTIONS

	OPTIONS[key] = value


def register_args(program : ArgumentParser) -> None:
	group_frame_processors = find_argument_group(program, 'frame processors')
	if group_frame_processors:
		group_frame_processors.add_argument('--frame-colorizer-model', help = wording.get('help.frame_colorizer_model'), default = config.get_str_value('frame_processors.frame_colorizer_model', 'ddcolor'), choices = frame_processors_choices.frame_colorizer_models)
		group_frame_processors.add_argument('--frame-colorizer-blend', help = wording.get('help.frame_colorizer_blend'), type = int, default = config.get_int_value('frame_processors.frame_colorizer_blend', '100'), choices = frame_processors_choices.frame_colorizer_blend_range, metavar = create_metavar(frame_processors_choices.frame_colorizer_blend_range))
		group_frame_processors.add_argument('--frame-colorizer-size', help = wording.get('help.frame_colorizer_size'), type = str, default = config.get_str_value('frame_processors.frame_colorizer_size', '256x256'), choices = frame_processors_choices.frame_colorizer_sizes)
		facefusion.jobs.job_store.register_step_keys([ 'frame_colorizer_model', 'frame_colorizer_blend', 'frame_colorizer_size' ])


def apply_args(args : Args) -> None:
	state_manager.init_item('frame_colorizer_model', args.get('frame_colorizer_model'))
	state_manager.init_item('frame_colorizer_blend', args.get('frame_colorizer_blend'))
	state_manager.init_item('frame_colorizer_size', args.get('frame_colorizer_size'))


def pre_check() -> bool:
	download_directory_path = resolve_relative_path('../.assets/models')
	model_url = get_options('model').get('url')
	model_path = get_options('model').get('path')

	if not state_manager.get_item('skip_download'):
		process_manager.check()
		conditional_download(download_directory_path, [ model_url ])
		process_manager.end()
	return is_file(model_path)


def post_check() -> bool:
	model_url = get_options('model').get('url')
	model_path = get_options('model').get('path')

	if not state_manager.get_item('skip_download') and not is_download_done(model_url, model_path):
		logger.error(wording.get('model_download_not_done') + wording.get('exclamation_mark'), NAME)
		return False
	if not is_file(model_path):
		logger.error(wording.get('model_file_not_present') + wording.get('exclamation_mark'), NAME)
		return False
	return True


def pre_process(mode : ProcessMode) -> bool:
	if mode in [ 'output', 'preview' ] and not is_image(state_manager.get_item('target_path')) and not is_video(state_manager.get_item('target_path')):
		logger.error(wording.get('choose_image_or_video_target') + wording.get('exclamation_mark'), NAME)
		return False
	if mode == 'output' and not in_directory(state_manager.get_item('output_path')):
		logger.error(wording.get('specify_image_or_video_output') + wording.get('exclamation_mark'), NAME)
		return False
	if mode == 'output' and not same_file_extension([ state_manager.get_item('target_path'), state_manager.get_item('output_path') ]):
		logger.error(wording.get('match_target_and_output_extension') + wording.get('exclamation_mark'), NAME)
		return False
	return True


def post_process() -> None:
	read_static_image.cache_clear()
	if state_manager.get_item('video_memory_strategy') in [ 'strict', 'moderate' ]:
		clear_frame_processor()
	if state_manager.get_item('video_memory_strategy') == 'strict':
		clear_face_analyser()
		clear_content_analyser()


def colorize_frame(temp_vision_frame : VisionFrame) -> VisionFrame:
	frame_processor = get_frame_processor()
	prepare_vision_frame = prepare_temp_frame(temp_vision_frame)

	with thread_semaphore():
		color_vision_frame = frame_processor.run(None,
		{
			frame_processor.get_inputs()[0].name: prepare_vision_frame
		})[0][0]

	color_vision_frame = merge_color_frame(temp_vision_frame, color_vision_frame)
	color_vision_frame = blend_frame(temp_vision_frame, color_vision_frame)
	return color_vision_frame


def prepare_temp_frame(temp_vision_frame : VisionFrame) -> VisionFrame:
	model_size = unpack_resolution(state_manager.get_item('frame_colorizer_size'))
	model_type = get_options('model').get('type')
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
	model_type = get_options('model').get('type')
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
	frame_processors.multi_process_frames(None, temp_frame_paths, process_frames)
