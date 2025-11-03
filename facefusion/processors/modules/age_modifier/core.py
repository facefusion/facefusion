from argparse import ArgumentParser
from functools import lru_cache

import cv2
import numpy

import facefusion.choices
import facefusion.jobs.job_manager
import facefusion.jobs.job_store
from facefusion import config, content_analyser, face_classifier, face_detector, face_landmarker, face_masker, face_recognizer, inference_manager, logger, state_manager, translator, video_manager
from facefusion.common_helper import create_int_metavar, is_macos
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.execution import has_execution_provider
from facefusion.face_analyser import scale_face
from facefusion.face_helper import merge_matrix, paste_back, scale_face_landmark_5, warp_face_by_face_landmark_5
from facefusion.face_masker import create_box_mask, create_occlusion_mask
from facefusion.face_selector import select_faces
from facefusion.filesystem import in_directory, is_image, is_video, resolve_relative_path, same_file_extension
from facefusion.processors.modules.age_modifier import choices as age_modifier_choices
from facefusion.processors.modules.age_modifier.types import AgeModifierDirection, AgeModifierInputs
from facefusion.processors.types import ProcessorOutputs
from facefusion.program_helper import find_argument_group
from facefusion.thread_helper import thread_semaphore
from facefusion.types import ApplyStateItem, Args, DownloadScope, Face, InferencePool, ModelOptions, ModelSet, ProcessMode, VisionFrame
from facefusion.vision import match_frame_color, read_static_image, read_static_video_frame


@lru_cache()
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
	return\
	{
		'styleganex_age':
		{
			'__metadata__':
			{
				'vendor': 'williamyang1991',
				'license': 'S-Lab-1.0',
				'year': 2023
			},
			'hashes':
			{
				'age_modifier':
				{
					'url': resolve_download_url('models-3.1.0', 'styleganex_age.hash'),
					'path': resolve_relative_path('../.assets/models/styleganex_age.hash')
				}
			},
			'sources':
			{
				'age_modifier':
				{
					'url': resolve_download_url('models-3.1.0', 'styleganex_age.onnx'),
					'path': resolve_relative_path('../.assets/models/styleganex_age.onnx')
				}
			},
			'templates':
			{
				'target': 'ffhq_512',
				'target_with_background': 'styleganex_384'
			},
			'sizes':
			{
				'target': (256, 256),
				'target_with_background': (384, 384)
			}
		}
	}


def get_inference_pool() -> InferencePool:
	model_names = [ state_manager.get_item('age_modifier_model') ]
	model_source_set = get_model_options().get('sources')

	return inference_manager.get_inference_pool(__name__, model_names, model_source_set)


def clear_inference_pool() -> None:
	model_names = [ state_manager.get_item('age_modifier_model') ]
	inference_manager.clear_inference_pool(__name__, model_names)


def get_model_options() -> ModelOptions:
	model_name = state_manager.get_item('age_modifier_model')
	return create_static_model_set('full').get(model_name)


def register_args(program : ArgumentParser) -> None:
	group_processors = find_argument_group(program, 'processors')
	if group_processors:
		group_processors.add_argument('--age-modifier-model', help = translator.get('help.model', __package__), default = config.get_str_value('processors', 'age_modifier_model', 'styleganex_age'), choices = age_modifier_choices.age_modifier_models)
		group_processors.add_argument('--age-modifier-direction', help = translator.get('help.direction', __package__), type = int, default = config.get_int_value('processors', 'age_modifier_direction', '0'), choices = age_modifier_choices.age_modifier_direction_range, metavar = create_int_metavar(age_modifier_choices.age_modifier_direction_range))
		facefusion.jobs.job_store.register_step_keys([ 'age_modifier_model', 'age_modifier_direction' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('age_modifier_model', args.get('age_modifier_model'))
	apply_state_item('age_modifier_direction', args.get('age_modifier_direction'))


def pre_check() -> bool:
	model_hash_set = get_model_options().get('hashes')
	model_source_set = get_model_options().get('sources')

	return conditional_download_hashes(model_hash_set) and conditional_download_sources(model_source_set)


def pre_process(mode : ProcessMode) -> bool:
	if mode in [ 'output', 'preview' ] and not is_image(state_manager.get_item('target_path')) and not is_video(state_manager.get_item('target_path')):
		logger.error(translator.get('choose_image_or_video_target') + translator.get('exclamation_mark'), __name__)
		return False
	if mode == 'output' and not in_directory(state_manager.get_item('output_path')):
		logger.error(translator.get('specify_image_or_video_output') + translator.get('exclamation_mark'), __name__)
		return False
	if mode == 'output' and not same_file_extension(state_manager.get_item('target_path'), state_manager.get_item('output_path')):
		logger.error(translator.get('match_target_and_output_extension') + translator.get('exclamation_mark'), __name__)
		return False
	return True


def post_process() -> None:
	read_static_image.cache_clear()
	read_static_video_frame.cache_clear()
	video_manager.clear_video_pool()
	if state_manager.get_item('video_memory_strategy') in [ 'strict', 'moderate' ]:
		clear_inference_pool()
	if state_manager.get_item('video_memory_strategy') == 'strict':
		content_analyser.clear_inference_pool()
		face_classifier.clear_inference_pool()
		face_detector.clear_inference_pool()
		face_landmarker.clear_inference_pool()
		face_masker.clear_inference_pool()
		face_recognizer.clear_inference_pool()


def modify_age(target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	model_templates = get_model_options().get('templates')
	model_sizes = get_model_options().get('sizes')
	face_landmark_5 = target_face.landmark_set.get('5/68').copy()
	crop_vision_frame, affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, face_landmark_5, model_templates.get('target'), model_sizes.get('target'))
	extend_face_landmark_5 = scale_face_landmark_5(face_landmark_5, 0.875)
	extend_vision_frame, extend_affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, extend_face_landmark_5, model_templates.get('target_with_background'), model_sizes.get('target_with_background'))
	extend_vision_frame_raw = extend_vision_frame.copy()
	box_mask = create_box_mask(extend_vision_frame, state_manager.get_item('face_mask_blur'), (0, 0, 0, 0))
	crop_masks =\
	[
		box_mask
	]

	if 'occlusion' in state_manager.get_item('face_mask_types'):
		occlusion_mask = create_occlusion_mask(crop_vision_frame)
		temp_matrix = merge_matrix([ extend_affine_matrix, cv2.invertAffineTransform(affine_matrix) ])
		occlusion_mask = cv2.warpAffine(occlusion_mask, temp_matrix, model_sizes.get('target_with_background'))
		crop_masks.append(occlusion_mask)

	crop_vision_frame = prepare_vision_frame(crop_vision_frame)
	extend_vision_frame = prepare_vision_frame(extend_vision_frame)
	age_modifier_direction = numpy.array(numpy.interp(state_manager.get_item('age_modifier_direction'), [ -100, 100 ], [ 2.5, -2.5 ])).astype(numpy.float32)
	extend_vision_frame = forward(crop_vision_frame, extend_vision_frame, age_modifier_direction)
	extend_vision_frame = normalize_extend_frame(extend_vision_frame)
	extend_vision_frame = match_frame_color(extend_vision_frame_raw, extend_vision_frame)
	extend_affine_matrix *= (model_sizes.get('target')[0] * 4) / model_sizes.get('target_with_background')[0]
	crop_mask = numpy.minimum.reduce(crop_masks).clip(0, 1)
	crop_mask = cv2.resize(crop_mask, (model_sizes.get('target')[0] * 4, model_sizes.get('target')[1] * 4))
	paste_vision_frame = paste_back(temp_vision_frame, extend_vision_frame, crop_mask, extend_affine_matrix)
	return paste_vision_frame


def forward(crop_vision_frame : VisionFrame, extend_vision_frame : VisionFrame, age_modifier_direction : AgeModifierDirection) -> VisionFrame:
	age_modifier = get_inference_pool().get('age_modifier')
	age_modifier_inputs = {}

	if is_macos() and has_execution_provider('coreml'):
		age_modifier.set_providers([ facefusion.choices.execution_provider_set.get('cpu') ])

	for age_modifier_input in age_modifier.get_inputs():
		if age_modifier_input.name == 'target':
			age_modifier_inputs[age_modifier_input.name] = crop_vision_frame
		if age_modifier_input.name == 'target_with_background':
			age_modifier_inputs[age_modifier_input.name] = extend_vision_frame
		if age_modifier_input.name == 'direction':
			age_modifier_inputs[age_modifier_input.name] = age_modifier_direction

	with thread_semaphore():
		crop_vision_frame = age_modifier.run(None, age_modifier_inputs)[0][0]

	return crop_vision_frame


def prepare_vision_frame(vision_frame : VisionFrame) -> VisionFrame:
	vision_frame = vision_frame[:, :, ::-1] / 255.0
	vision_frame = (vision_frame - 0.5) / 0.5
	vision_frame = numpy.expand_dims(vision_frame.transpose(2, 0, 1), axis = 0).astype(numpy.float32)
	return vision_frame


def normalize_extend_frame(extend_vision_frame : VisionFrame) -> VisionFrame:
	model_sizes = get_model_options().get('sizes')
	extend_vision_frame = numpy.clip(extend_vision_frame, -1, 1)
	extend_vision_frame = (extend_vision_frame + 1) / 2
	extend_vision_frame = extend_vision_frame.transpose(1, 2, 0).clip(0, 255)
	extend_vision_frame = (extend_vision_frame * 255.0)
	extend_vision_frame = extend_vision_frame.astype(numpy.uint8)[:, :, ::-1]
	extend_vision_frame = cv2.resize(extend_vision_frame, (model_sizes.get('target')[0] * 4, model_sizes.get('target')[1] * 4), interpolation = cv2.INTER_AREA)
	return extend_vision_frame


def process_frame(inputs : AgeModifierInputs) -> ProcessorOutputs:
	reference_vision_frame = inputs.get('reference_vision_frame')
	target_vision_frame = inputs.get('target_vision_frame')
	temp_vision_frame = inputs.get('temp_vision_frame')
	temp_vision_mask = inputs.get('temp_vision_mask')
	target_faces = select_faces(reference_vision_frame, target_vision_frame)

	if target_faces:
		for target_face in target_faces:
			target_face = scale_face(target_face, target_vision_frame, temp_vision_frame)
			temp_vision_frame = modify_age(target_face, temp_vision_frame)

	return temp_vision_frame, temp_vision_mask
