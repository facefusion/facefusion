from argparse import ArgumentParser
from time import sleep
from typing import Any, List, Literal, Optional

import cv2
import numpy
import onnxruntime
from cv2.typing import Size
from numpy.typing import NDArray

import facefusion.jobs.job_manager
import facefusion.jobs.job_store
import facefusion.processors.frame.core as frame_processors
from facefusion import config, logger, process_manager, state_manager, wording
from facefusion.common_helper import create_metavar, map_float
from facefusion.content_analyser import clear_content_analyser
from facefusion.download import conditional_download, is_download_done
from facefusion.execution import apply_execution_provider_options
from facefusion.face_analyser import clear_face_analyser, get_many_faces, get_one_face
from facefusion.face_helper import merge_matrix, paste_back, warp_face_by_face_landmark_5
from facefusion.face_masker import clear_face_occluder, create_occlusion_mask, create_static_box_mask
from facefusion.face_selector import find_similar_faces, sort_and_filter_faces
from facefusion.face_store import get_reference_faces
from facefusion.filesystem import in_directory, is_file, is_image, is_video, resolve_relative_path, same_file_extension
from facefusion.processors.frame import choices as frame_processors_choices
from facefusion.processors.frame.typing import AgeModifierInputs
from facefusion.program_helper import find_argument_group
from facefusion.thread_helper import thread_lock, thread_semaphore
from facefusion.typing import Args, Face, Mask, ModelSet, OptionsWithModel, ProcessMode, QueuePayload, UpdateProgress, VisionFrame
from facefusion.vision import read_image, read_static_image, write_image

FRAME_PROCESSOR = None
NAME = __name__.upper()
MODELS : ModelSet =\
{
	'styleganex_age':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/styleganex_age.onnx',
		'path': resolve_relative_path('../.assets/models/styleganex_age.onnx'),
		'template': 'ffhq_512',
		'size': (512, 512)
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
			FRAME_PROCESSOR = onnxruntime.InferenceSession(model_path, providers = apply_execution_provider_options(state_manager.get_item('execution_device_id'), state_manager.get_item('execution_providers')))
	return FRAME_PROCESSOR


def clear_frame_processor() -> None:
	global FRAME_PROCESSOR

	FRAME_PROCESSOR = None


def get_options(key : Literal['model']) -> Any:
	global OPTIONS

	if OPTIONS is None:
		OPTIONS =\
		{
			'model': MODELS[state_manager.get_item('age_modifier_model')]
		}
	return OPTIONS.get(key)


def set_options(key : Literal['model'], value : Any) -> None:
	global OPTIONS

	OPTIONS[key] = value


def register_args(program : ArgumentParser) -> None:
	group_frame_processors = find_argument_group(program, 'frame processors')
	if group_frame_processors:
		group_frame_processors.add_argument('--age-modifier-model', help = wording.get('help.age_modifier_model'), default = config.get_str_value('frame_processors.age_modifier_model', 'styleganex_age'), choices = frame_processors_choices.age_modifier_models)
		group_frame_processors.add_argument('--age-modifier-direction', help = wording.get('help.age_modifier_direction'), type = int, default = config.get_int_value('frame_processors.age_modifier_direction', '0'), choices = frame_processors_choices.age_modifier_direction_range, metavar = create_metavar(frame_processors_choices.age_modifier_direction_range))
		facefusion.jobs.job_store.register_step_keys([ 'age_modifier_model', 'age_modifier_direction' ])


def apply_args(args : Args) -> None:
	state_manager.init_item('age_modifier_model', args.get('age_modifier_model'))
	state_manager.init_item('age_modifier_direction', args.get('age_modifier_direction'))


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
		clear_face_occluder()


def modify_age(target_face: Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	model_template = get_options('model').get('template')
	model_size = get_options('model').get('size')
	face_landmark_5 = target_face.landmark_set.get('5/68').copy()
	extend_face_landmark_5 = (face_landmark_5 - face_landmark_5[2]) * 2 + face_landmark_5[2]
	crop_vision_frame, affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, face_landmark_5, model_template, (256, 256))
	extend_vision_frame, extend_affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, extend_face_landmark_5, model_template, model_size)
	extend_vision_frame_raw = extend_vision_frame.copy()
	box_mask = create_static_box_mask(model_size, state_manager.get_item('face_mask_blur'), (0, 0, 0, 0))
	crop_masks =\
	[
		box_mask
	]

	if 'occlusion' in state_manager.get_item('face_mask_types'):
		occlusion_mask = create_occlusion_mask(crop_vision_frame)
		combined_matrix = merge_matrix([ extend_affine_matrix, cv2.invertAffineTransform(affine_matrix) ])
		occlusion_mask = cv2.warpAffine(occlusion_mask, combined_matrix, model_size)
		crop_masks.append(occlusion_mask)
	crop_vision_frame = prepare_vision_frame(crop_vision_frame)
	extend_vision_frame = prepare_vision_frame(extend_vision_frame)
	extend_vision_frame = apply_age(crop_vision_frame, extend_vision_frame)
	extend_vision_frame = normalize_extend_frame(extend_vision_frame)
	extend_vision_frame = fix_color(extend_vision_frame_raw, extend_vision_frame)
	extend_crop_mask = cv2.pyrUp(numpy.minimum.reduce(crop_masks).clip(0, 1))
	extend_affine_matrix *= extend_vision_frame.shape[0] / 512
	paste_vision_frame = paste_back(temp_vision_frame, extend_vision_frame, extend_crop_mask, extend_affine_matrix)
	return paste_vision_frame


def fix_color(extend_vision_frame_raw : VisionFrame, extend_vision_frame : VisionFrame) -> VisionFrame:
	color_difference = compute_color_difference(extend_vision_frame_raw, extend_vision_frame, (48, 48))
	color_difference_mask = create_static_box_mask(extend_vision_frame.shape[:2][::-1], 1.0, (0, 0, 0, 0))
	color_difference_mask = numpy.stack((color_difference_mask, ) * 3, axis = -1)
	extend_vision_frame = normalize_color_difference(color_difference, color_difference_mask, extend_vision_frame)
	return extend_vision_frame


def compute_color_difference(extend_vision_frame_raw : VisionFrame, extend_vision_frame : VisionFrame, size : Size) -> VisionFrame:
	extend_vision_frame_raw = extend_vision_frame_raw.astype(numpy.float32) / 255
	extend_vision_frame_raw = cv2.resize(extend_vision_frame_raw, size, interpolation = cv2.INTER_AREA)
	extend_vision_frame = extend_vision_frame.astype(numpy.float32) / 255
	extend_vision_frame = cv2.resize(extend_vision_frame, size, interpolation = cv2.INTER_AREA)
	color_difference = extend_vision_frame_raw - extend_vision_frame
	return color_difference


def normalize_color_difference(color_difference : VisionFrame, color_difference_mask : Mask, extend_vision_frame : VisionFrame) -> VisionFrame:
	color_difference = cv2.resize(color_difference, extend_vision_frame.shape[:2][::-1], interpolation = cv2.INTER_CUBIC)
	color_difference_mask = 1 - color_difference_mask.clip(0, 0.75)
	extend_vision_frame = extend_vision_frame.astype(numpy.float32) / 255
	extend_vision_frame += color_difference * color_difference_mask
	extend_vision_frame = extend_vision_frame.clip(0, 1)
	extend_vision_frame = numpy.multiply(extend_vision_frame, 255).astype(numpy.uint8)
	return extend_vision_frame


def apply_age(crop_vision_frame : VisionFrame, crop_vision_frame_extended : VisionFrame) -> VisionFrame:
	frame_processor = get_frame_processor()
	frame_processor_inputs = {}

	for frame_processor_input in frame_processor.get_inputs():
		if frame_processor_input.name == 'target':
			frame_processor_inputs[frame_processor_input.name] = crop_vision_frame
		if frame_processor_input.name == 'target_with_background':
			frame_processor_inputs[frame_processor_input.name] = crop_vision_frame_extended
		if frame_processor_input.name == 'direction':
			frame_processor_inputs[frame_processor_input.name] = prepare_direction(state_manager.get_item('age_modifier_direction'))

	with thread_semaphore():
		crop_vision_frame = frame_processor.run(None, frame_processor_inputs)[0][0]

	return crop_vision_frame


def prepare_direction(direction : int) -> NDArray[Any]:
	direction = map_float(float(direction), -100, 100, 2.5, -2.5) #type:ignore[assignment]
	return numpy.array(direction).astype(numpy.float32)


def prepare_vision_frame(vision_frame : VisionFrame) -> VisionFrame:
	vision_frame = vision_frame[:, :, ::-1] / 255.0
	vision_frame = (vision_frame - 0.5) / 0.5
	vision_frame = numpy.expand_dims(vision_frame.transpose(2, 0, 1), axis = 0).astype(numpy.float32)
	return vision_frame


def normalize_extend_frame(extend_vision_frame : VisionFrame) -> VisionFrame:
	extend_vision_frame = numpy.clip(extend_vision_frame, -1, 1)
	extend_vision_frame = (extend_vision_frame + 1) / 2
	extend_vision_frame = extend_vision_frame.transpose(1, 2, 0).clip(0, 255)
	extend_vision_frame = (extend_vision_frame * 255.0)
	extend_vision_frame = extend_vision_frame.astype(numpy.uint8)[:, :, ::-1]
	extend_vision_frame = cv2.pyrDown(extend_vision_frame)
	return extend_vision_frame


def get_reference_frame(source_face : Face, target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	return modify_age(target_face, temp_vision_frame)


def process_frame(inputs : AgeModifierInputs) -> VisionFrame:
	reference_faces = inputs.get('reference_faces')
	target_vision_frame = inputs.get('target_vision_frame')
	many_faces = sort_and_filter_faces(get_many_faces([ target_vision_frame ]))

	if state_manager.get_item('face_selector_mode') == 'many':
		if many_faces:
			for target_face in many_faces:
				target_vision_frame = modify_age(target_face, target_vision_frame)
	if state_manager.get_item('face_selector_mode') == 'one':
		target_face = get_one_face(many_faces)
		if target_face:
			target_vision_frame = modify_age(target_face, target_vision_frame)
	if state_manager.get_item('face_selector_mode') == 'reference':
		similar_faces = find_similar_faces(many_faces, reference_faces, state_manager.get_item('reference_face_distance'))
		if similar_faces:
			for similar_face in similar_faces:
				target_vision_frame = modify_age(similar_face, target_vision_frame)
	return target_vision_frame


def process_frames(source_path : List[str], queue_payloads : List[QueuePayload], update_progress : UpdateProgress) -> None:
	reference_faces = get_reference_faces() if 'reference' in state_manager.get_item('face_selector_mode') else None

	for queue_payload in process_manager.manage(queue_payloads):
		target_vision_path = queue_payload['frame_path']
		target_vision_frame = read_image(target_vision_path)
		output_vision_frame = process_frame(
		{
			'reference_faces': reference_faces,
			'target_vision_frame': target_vision_frame
		})
		write_image(target_vision_path, output_vision_frame)
		update_progress(1)


def process_image(source_path : str, target_path : str, output_path : str) -> None:
	reference_faces = get_reference_faces() if 'reference' in state_manager.get_item('face_selector_mode') else None
	target_vision_frame = read_static_image(target_path)
	output_vision_frame = process_frame(
	{
		'reference_faces': reference_faces,
		'target_vision_frame': target_vision_frame
	})
	write_image(output_path, output_vision_frame)


def process_video(source_paths : List[str], temp_frame_paths : List[str]) -> None:
	frame_processors.multi_process_frames(None, temp_frame_paths, process_frames)
