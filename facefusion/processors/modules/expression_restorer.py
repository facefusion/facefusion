from argparse import ArgumentParser
from functools import lru_cache
from typing import Tuple

import cv2
import numpy

import facefusion.jobs.job_manager
import facefusion.jobs.job_store
from facefusion import config, content_analyser, face_classifier, face_detector, face_landmarker, face_masker, face_recognizer, inference_manager, logger, state_manager, video_manager, wording
from facefusion.common_helper import create_int_metavar
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.face_analyser import scale_face
from facefusion.face_helper import paste_back, warp_face_by_face_landmark_5
from facefusion.face_masker import create_box_mask, create_occlusion_mask
from facefusion.face_selector import select_faces
from facefusion.filesystem import in_directory, is_image, is_video, resolve_relative_path, same_file_extension
from facefusion.processors import choices as processors_choices
from facefusion.processors.live_portrait import create_rotation, limit_expression
from facefusion.processors.types import ExpressionRestorerInputs, LivePortraitExpression, LivePortraitFeatureVolume, LivePortraitMotionPoints, LivePortraitPitch, LivePortraitRoll, LivePortraitScale, LivePortraitTranslation, LivePortraitYaw
from facefusion.program_helper import find_argument_group
from facefusion.thread_helper import conditional_thread_semaphore, thread_semaphore
from facefusion.types import ApplyStateItem, Args, DownloadScope, Face, InferencePool, ModelOptions, ModelSet, ProcessMode, VisionFrame
from facefusion.vision import read_static_image, read_static_video_frame


@lru_cache()
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
	return\
	{
		'live_portrait':
		{
			'hashes':
			{
				'feature_extractor':
				{
					'url': resolve_download_url('models-3.0.0', 'live_portrait_feature_extractor.hash'),
					'path': resolve_relative_path('../.assets/models/live_portrait_feature_extractor.hash')
				},
				'motion_extractor':
				{
					'url': resolve_download_url('models-3.0.0', 'live_portrait_motion_extractor.hash'),
					'path': resolve_relative_path('../.assets/models/live_portrait_motion_extractor.hash')
				},
				'generator':
				{
					'url': resolve_download_url('models-3.0.0', 'live_portrait_generator.hash'),
					'path': resolve_relative_path('../.assets/models/live_portrait_generator.hash')
				}
			},
			'sources':
			{
				'feature_extractor':
				{
					'url': resolve_download_url('models-3.0.0', 'live_portrait_feature_extractor.onnx'),
					'path': resolve_relative_path('../.assets/models/live_portrait_feature_extractor.onnx')
				},
				'motion_extractor':
				{
					'url': resolve_download_url('models-3.0.0', 'live_portrait_motion_extractor.onnx'),
					'path': resolve_relative_path('../.assets/models/live_portrait_motion_extractor.onnx')
				},
				'generator':
				{
					'url': resolve_download_url('models-3.0.0', 'live_portrait_generator.onnx'),
					'path': resolve_relative_path('../.assets/models/live_portrait_generator.onnx')
				}
			},
			'template': 'arcface_128',
			'size': (512, 512)
		}
	}


def get_inference_pool() -> InferencePool:
	model_names = [ state_manager.get_item('expression_restorer_model') ]
	model_source_set = get_model_options().get('sources')

	return inference_manager.get_inference_pool(__name__, model_names, model_source_set)


def clear_inference_pool() -> None:
	model_names = [ state_manager.get_item('expression_restorer_model') ]
	inference_manager.clear_inference_pool(__name__, model_names)


def get_model_options() -> ModelOptions:
	model_name = state_manager.get_item('expression_restorer_model')
	return create_static_model_set('full').get(model_name)


def register_args(program : ArgumentParser) -> None:
	group_processors = find_argument_group(program, 'processors')
	if group_processors:
		group_processors.add_argument('--expression-restorer-model', help = wording.get('help.expression_restorer_model'), default = config.get_str_value('processors', 'expression_restorer_model', 'live_portrait'), choices = processors_choices.expression_restorer_models)
		group_processors.add_argument('--expression-restorer-factor', help = wording.get('help.expression_restorer_factor'), type = int, default = config.get_int_value('processors', 'expression_restorer_factor', '80'), choices = processors_choices.expression_restorer_factor_range, metavar = create_int_metavar(processors_choices.expression_restorer_factor_range))
		group_processors.add_argument('--expression-restorer-areas', help = wording.get('help.expression_restorer_areas').format(choices = ', '.join(processors_choices.expression_restorer_areas)), default = config.get_str_list('processors', 'expression_restorer_areas', ' '.join(processors_choices.expression_restorer_areas)), choices = processors_choices.expression_restorer_areas, nargs = '+', metavar = 'EXPRESSION_RESTORER_AREAS')
		facefusion.jobs.job_store.register_step_keys([ 'expression_restorer_model', 'expression_restorer_factor', 'expression_restorer_areas' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('expression_restorer_model', args.get('expression_restorer_model'))
	apply_state_item('expression_restorer_factor', args.get('expression_restorer_factor'))
	apply_state_item('expression_restorer_areas', args.get('expression_restorer_areas'))


def pre_check() -> bool:
	model_hash_set = get_model_options().get('hashes')
	model_source_set = get_model_options().get('sources')

	return conditional_download_hashes(model_hash_set) and conditional_download_sources(model_source_set)


def pre_process(mode : ProcessMode) -> bool:
	if mode == 'stream':
		logger.error(wording.get('stream_not_supported') + wording.get('exclamation_mark'), __name__)
		return False
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


def restore_expression(target_face : Face, target_vision_frame : VisionFrame, temp_vision_frame : VisionFrame) -> VisionFrame:
	model_template = get_model_options().get('template')
	model_size = get_model_options().get('size')
	expression_restorer_factor = float(numpy.interp(float(state_manager.get_item('expression_restorer_factor')), [ 0, 100 ], [ 0, 1.2 ]))
	target_crop_vision_frame, _ = warp_face_by_face_landmark_5(target_vision_frame, target_face.landmark_set.get('5/68'), model_template, model_size)
	temp_crop_vision_frame, affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, target_face.landmark_set.get('5/68'), model_template, model_size)
	box_mask = create_box_mask(temp_crop_vision_frame, state_manager.get_item('face_mask_blur'), (0, 0, 0, 0))
	crop_masks =\
	[
		box_mask
	]

	if 'occlusion' in state_manager.get_item('face_mask_types'):
		occlusion_mask = create_occlusion_mask(temp_crop_vision_frame)
		crop_masks.append(occlusion_mask)

	target_crop_vision_frame = prepare_crop_frame(target_crop_vision_frame)
	temp_crop_vision_frame = prepare_crop_frame(temp_crop_vision_frame)
	temp_crop_vision_frame = apply_restore(target_crop_vision_frame, temp_crop_vision_frame, expression_restorer_factor)
	temp_crop_vision_frame = normalize_crop_frame(temp_crop_vision_frame)
	crop_mask = numpy.minimum.reduce(crop_masks).clip(0, 1)
	paste_vision_frame = paste_back(temp_vision_frame, temp_crop_vision_frame, crop_mask, affine_matrix)
	return paste_vision_frame


def apply_restore(target_crop_vision_frame : VisionFrame, temp_crop_vision_frame : VisionFrame, expression_restorer_factor : float) -> VisionFrame:
	feature_volume = forward_extract_feature(temp_crop_vision_frame)
	target_expression = forward_extract_motion(target_crop_vision_frame)[5]
	pitch, yaw, roll, scale, translation, temp_expression, motion_points = forward_extract_motion(temp_crop_vision_frame)
	rotation = create_rotation(pitch, yaw, roll)
	target_expression = restrict_expression_areas(temp_expression, target_expression)
	target_expression = target_expression * expression_restorer_factor + temp_expression * (1 - expression_restorer_factor)
	target_expression = limit_expression(target_expression)
	target_motion_points = scale * (motion_points @ rotation.T + target_expression) + translation
	temp_motion_points = scale * (motion_points @ rotation.T + temp_expression) + translation
	crop_vision_frame = forward_generate_frame(feature_volume, target_motion_points, temp_motion_points)
	return crop_vision_frame


def restrict_expression_areas(temp_expression : LivePortraitExpression, target_expression : LivePortraitExpression) -> LivePortraitExpression:
	expression_restorer_areas = state_manager.get_item('expression_restorer_areas')

	if 'upper-face' not in expression_restorer_areas:
		target_expression[:, [1, 2, 6, 10, 11, 12, 13, 15, 16]] = temp_expression[:, [1, 2, 6, 10, 11, 12, 13, 15, 16]]

	if 'lower-face' not in expression_restorer_areas:
		target_expression[:, [3, 7, 14, 17, 18, 19, 20]] = temp_expression[:, [3, 7, 14, 17, 18, 19, 20]]

	target_expression[:, [0, 4, 5, 8, 9]] = temp_expression[:, [0, 4, 5, 8, 9]]
	return target_expression


def forward_extract_feature(crop_vision_frame : VisionFrame) -> LivePortraitFeatureVolume:
	feature_extractor = get_inference_pool().get('feature_extractor')

	with conditional_thread_semaphore():
		feature_volume = feature_extractor.run(None,
		{
			'input': crop_vision_frame
		})[0]

	return feature_volume


def forward_extract_motion(crop_vision_frame : VisionFrame) -> Tuple[LivePortraitPitch, LivePortraitYaw, LivePortraitRoll, LivePortraitScale, LivePortraitTranslation, LivePortraitExpression, LivePortraitMotionPoints]:
	motion_extractor = get_inference_pool().get('motion_extractor')

	with conditional_thread_semaphore():
		pitch, yaw, roll, scale, translation, expression, motion_points = motion_extractor.run(None,
		{
			'input': crop_vision_frame
		})

	return pitch, yaw, roll, scale, translation, expression, motion_points


def forward_generate_frame(feature_volume : LivePortraitFeatureVolume, target_motion_points : LivePortraitMotionPoints, temp_motion_points : LivePortraitMotionPoints) -> VisionFrame:
	generator = get_inference_pool().get('generator')

	with thread_semaphore():
		crop_vision_frame = generator.run(None,
		{
			'feature_volume': feature_volume,
			'source': target_motion_points,
			'target': temp_motion_points
		})[0][0]

	return crop_vision_frame


def prepare_crop_frame(crop_vision_frame : VisionFrame) -> VisionFrame:
	model_size = get_model_options().get('size')
	prepare_size = (model_size[0] // 2, model_size[1] // 2)
	crop_vision_frame = cv2.resize(crop_vision_frame, prepare_size, interpolation = cv2.INTER_AREA)
	crop_vision_frame = crop_vision_frame[:, :, ::-1] / 255.0
	crop_vision_frame = numpy.expand_dims(crop_vision_frame.transpose(2, 0, 1), axis = 0).astype(numpy.float32)
	return crop_vision_frame


def normalize_crop_frame(crop_vision_frame : VisionFrame) -> VisionFrame:
	crop_vision_frame = crop_vision_frame.transpose(1, 2, 0).clip(0, 1)
	crop_vision_frame = crop_vision_frame * 255.0
	crop_vision_frame = crop_vision_frame.astype(numpy.uint8)[:, :, ::-1]
	return crop_vision_frame


def process_frame(inputs : ExpressionRestorerInputs) -> VisionFrame:
	reference_vision_frame = inputs.get('reference_vision_frame')
	target_vision_frame = inputs.get('target_vision_frame')
	temp_vision_frame = inputs.get('temp_vision_frame')
	target_faces = select_faces(reference_vision_frame, target_vision_frame)

	if target_faces:
		for target_face in target_faces:
			target_face = scale_face(target_face, target_vision_frame, temp_vision_frame)
			temp_vision_frame = restore_expression(target_face, target_vision_frame, temp_vision_frame)

	return temp_vision_frame
