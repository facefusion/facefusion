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
from facefusion.common_helper import create_metavar, map_float_range
from facefusion.content_analyser import clear_content_analyser
from facefusion.download import conditional_download, is_download_done
from facefusion.execution import apply_execution_provider_options
from facefusion.face_analyser import clear_face_analyser, get_many_faces, get_one_face
from facefusion.face_helper import combine_two_matrix, paste_back, warp_face_by_face_landmark_5
from facefusion.face_masker import clear_face_occluder, create_occlusion_mask, create_static_box_mask
from facefusion.face_selector import find_similar_faces, sort_and_filter_faces
from facefusion.face_store import get_reference_faces
from facefusion.filesystem import in_directory, is_file, is_image, is_video, resolve_relative_path, same_file_extension
from facefusion.processors.frame import choices as frame_processors_choices
from facefusion.processors.frame.typing import AgeModifierInputs
from facefusion.program_helper import find_argument_group
from facefusion.thread_helper import thread_lock, thread_semaphore
from facefusion.typing import Face, ModelSet, OptionsWithModel, ProcessMode, QueuePayload, UpdateProgress, VisionFrame
from facefusion.vision import read_image, read_static_image, write_image

FRAME_PROCESSOR = None
NAME = __name__.upper()
MODELS : ModelSet =\
{
	'styleganex':
	{
		'url': '...',
		'path': resolve_relative_path('../.assets/models/age_modifier_styleganex.onnx'),
		'template': 'ffhq_512',
		'size': (512, 512)
	},
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
		group_frame_processors.add_argument('--age-modifier-model', help = wording.get('help.age_modifier_model'), default = config.get_str_value('frame_processors.age_modifier_model', 'styleganex'), choices = frame_processors_choices.age_modifier_models)
		group_frame_processors.add_argument('--age-modifier-direction', help = wording.get('help.age_modifier_direction'), type = int, default = config.get_int_value('frame_processors.age_modifier_direction', '0'), choices = frame_processors_choices.age_modifier_direction_range, metavar = create_metavar(frame_processors_choices.age_modifier_direction_range))
		facefusion.jobs.job_store.register_step_keys([ 'age_modifier_model', 'age_modifier_direction' ])


def apply_args(program : ArgumentParser) -> None:
	args = program.parse_args()
	state_manager.init_item('age_modifier_model', args.age_modifier_model)
	state_manager.init_item('age_modifier_direction', args.age_modifier_direction)


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
	face_landmark_5_extended = (face_landmark_5 - face_landmark_5[2]) * 2 + face_landmark_5[2]
	crop_vision_frame, affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, face_landmark_5, model_template, (256, 256))
	crop_vision_frame_extended, affine_matrix_extended = warp_face_by_face_landmark_5(temp_vision_frame, face_landmark_5_extended, model_template, model_size)
	crop_vision_frame_extended_raw = crop_vision_frame_extended.copy()
	box_mask = create_static_box_mask(model_size, state_manager.get_item('face_mask_blur'), (0, 0, 0, 0))
	crop_masks =\
	[
		box_mask
	]

	if 'occlusion' in state_manager.get_item('face_mask_types'):
		occlusion_mask = create_occlusion_mask(crop_vision_frame)
		combined_matrix = combine_two_matrix(affine_matrix_extended, cv2.invertAffineTransform(affine_matrix))
		occlusion_mask = cv2.warpAffine(occlusion_mask, combined_matrix, model_size)
		crop_masks.append(occlusion_mask)
	crop_vision_frame = prepare_crop_frame(crop_vision_frame)
	crop_vision_frame_extended = prepare_crop_frame(crop_vision_frame_extended)
	crop_vision_frame_extended = apply_age_modifier(crop_vision_frame, crop_vision_frame_extended)
	crop_vision_frame_extended = normalize_crop_frame(crop_vision_frame_extended)
	crop_vision_frame_extended = fix_color(crop_vision_frame_extended_raw, crop_vision_frame_extended)
	crop_mask = cv2.pyrUp(numpy.minimum.reduce(crop_masks).clip(0, 1))
	paste_vision_frame = paste_back(temp_vision_frame, crop_vision_frame_extended, crop_mask, affine_matrix_extended * 2)
	return paste_vision_frame


def fix_color(crop_vision_frame_extended_raw : VisionFrame, crop_vision_frame_extended : VisionFrame) -> VisionFrame:
	crop_vision_frame_extended_raw = crop_vision_frame_extended_raw.astype(numpy.float32) / 255
	crop_vision_frame_extended = crop_vision_frame_extended.astype(numpy.float32) / 255
	crop_vision_frame_extended_raw_downscaled = cv2.resize(crop_vision_frame_extended_raw, (48, 48), interpolation = cv2.INTER_AREA)
	crop_vision_frame_extended_downscaled = cv2.resize(crop_vision_frame_extended, (48, 48), interpolation = cv2.INTER_AREA)
	color_difference = crop_vision_frame_extended_raw_downscaled - crop_vision_frame_extended_downscaled
	color_difference = cv2.resize(color_difference, crop_vision_frame_extended.shape[:2][::-1], interpolation = cv2.INTER_CUBIC) #type:ignore[assignment]
	color_difference_mask = 1 - create_static_box_mask(crop_vision_frame_extended.shape[:2][::-1], 1.0, (0, 0, 0, 0))
	color_difference_mask = numpy.stack((color_difference_mask, ) * 3, axis = -1)
	crop_vision_frame_extended += (color_difference * color_difference_mask.clip(0, 0.75))
	crop_vision_frame_extended = crop_vision_frame_extended.clip(0, 1)
	crop_vision_frame_extended = numpy.multiply(crop_vision_frame_extended, 255).astype(numpy.uint8)
	return crop_vision_frame_extended


def apply_age_modifier(crop_vision_frame : VisionFrame, crop_vision_frame_extended : VisionFrame) -> VisionFrame:
	frame_processor = get_frame_processor()
	frame_processor_inputs = {}

	for frame_processor_input in frame_processor.get_inputs():
		if frame_processor_input.name == 'target':
			frame_processor_inputs[frame_processor_input.name] = crop_vision_frame
		if frame_processor_input.name == 'target_with_background':
			frame_processor_inputs[frame_processor_input.name] = crop_vision_frame_extended
		if frame_processor_input.name == 'direction':
			age_modifier_direction = map_float_range(state_manager.get_item('age_modifier_direction'), -100, 100, 2.5, -2.5)
			frame_processor_inputs[frame_processor_input.name] = numpy.array(age_modifier_direction, dtype = numpy.float32)

	with thread_semaphore():
		crop_vision_frame, latent = frame_processor.run(None, frame_processor_inputs)

	return crop_vision_frame[0]


def prepare_crop_frame(crop_vision_frame : VisionFrame) -> VisionFrame:
	crop_vision_frame = crop_vision_frame[:, :, ::-1] / 255.0
	crop_vision_frame = (crop_vision_frame - 0.5) / 0.5
	crop_vision_frame = numpy.expand_dims(crop_vision_frame.transpose(2, 0, 1), axis = 0).astype(numpy.float32)
	return crop_vision_frame


def normalize_crop_frame(crop_vision_frame : VisionFrame) -> VisionFrame:
	crop_vision_frame = numpy.clip(crop_vision_frame, -1, 1)
	crop_vision_frame = (crop_vision_frame + 1) / 2
	crop_vision_frame = crop_vision_frame.transpose(1, 2, 0).clip(0, 255)
	crop_vision_frame = (crop_vision_frame * 255.0)
	crop_vision_frame = crop_vision_frame.astype(numpy.uint8)[:, :, ::-1]
	crop_vision_frame = cv2.pyrDown(crop_vision_frame)
	return crop_vision_frame


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
