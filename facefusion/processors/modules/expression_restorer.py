from argparse import ArgumentParser
from functools import lru_cache
from typing import List, Tuple

import cv2
import numpy

import facefusion.jobs.job_manager
import facefusion.jobs.job_store
import facefusion.processors.core as processors
from facefusion import config, content_analyser, face_classifier, face_detector, face_landmarker, face_masker, face_recognizer, inference_manager, logger, process_manager, state_manager, video_manager, wording
from facefusion.common_helper import create_int_metavar
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.face_analyser import get_many_faces, get_one_face
from facefusion.face_helper import paste_back, warp_face_by_face_landmark_5
from facefusion.face_masker import create_box_mask, create_occlusion_mask
from facefusion.face_selector import find_similar_faces, sort_and_filter_faces
from facefusion.face_store import get_reference_faces
from facefusion.filesystem import in_directory, is_image, is_video, resolve_relative_path, same_file_extension
from facefusion.processors import choices as processors_choices
from facefusion.processors.live_portrait import create_rotation, limit_expression
from facefusion.processors.types import ExpressionRestorerInputs, LivePortraitExpression, LivePortraitFeatureVolume, LivePortraitMotionPoints, LivePortraitPitch, LivePortraitRoll, LivePortraitScale, LivePortraitTranslation, LivePortraitYaw
from facefusion.program_helper import find_argument_group
from facefusion.thread_helper import conditional_thread_semaphore, thread_semaphore
from facefusion.types import ApplyStateItem, Args, DownloadScope, Face, InferencePool, ModelOptions, ModelSet, ProcessMode, QueuePayload, UpdateProgress, VisionFrame
from facefusion.vision import read_image, read_static_image, read_video_frame, write_image


@lru_cache(maxsize = None)
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
		facefusion.jobs.job_store.register_step_keys([ 'expression_restorer_model', 'expression_restorer_factor' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('expression_restorer_model', args.get('expression_restorer_model'))
	apply_state_item('expression_restorer_factor', args.get('expression_restorer_factor'))


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


def restore_expression(source_vision_frame : VisionFrame, target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	model_template = get_model_options().get('template')
	model_size = get_model_options().get('size')
	expression_restorer_factor = float(numpy.interp(float(state_manager.get_item('expression_restorer_factor')), [ 0, 100 ], [ 0, 1.2 ]))
	source_vision_frame = cv2.resize(source_vision_frame, temp_vision_frame.shape[:2][::-1])
	source_crop_vision_frame, _ = warp_face_by_face_landmark_5(source_vision_frame, target_face.landmark_set.get('5/68'), model_template, model_size)
	target_crop_vision_frame, affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, target_face.landmark_set.get('5/68'), model_template, model_size)
	box_mask = create_box_mask(target_crop_vision_frame, state_manager.get_item('face_mask_blur'), (0, 0, 0, 0))
	crop_masks =\
	[
		box_mask
	]

	if 'occlusion' in state_manager.get_item('face_mask_types'):
		occlusion_mask = create_occlusion_mask(target_crop_vision_frame)
		crop_masks.append(occlusion_mask)

	source_crop_vision_frame = prepare_crop_frame(source_crop_vision_frame)
	target_crop_vision_frame = prepare_crop_frame(target_crop_vision_frame)
	target_crop_vision_frame = apply_restore(source_crop_vision_frame, target_crop_vision_frame, expression_restorer_factor)
	target_crop_vision_frame = normalize_crop_frame(target_crop_vision_frame)
	crop_mask = numpy.minimum.reduce(crop_masks).clip(0, 1)
	temp_vision_frame = paste_back(temp_vision_frame, target_crop_vision_frame, crop_mask, affine_matrix)
	return temp_vision_frame


def apply_restore(source_crop_vision_frame : VisionFrame, target_crop_vision_frame : VisionFrame, expression_restorer_factor : float) -> VisionFrame:
	feature_volume = forward_extract_feature(target_crop_vision_frame)
	source_expression = forward_extract_motion(source_crop_vision_frame)[5]
	pitch, yaw, roll, scale, translation, target_expression, motion_points = forward_extract_motion(target_crop_vision_frame)
	rotation = create_rotation(pitch, yaw, roll)
	source_expression[:, [ 0, 4, 5, 8, 9 ]] = target_expression[:, [ 0, 4, 5, 8, 9 ]]
	source_expression = source_expression * expression_restorer_factor + target_expression * (1 - expression_restorer_factor)
	source_expression = limit_expression(source_expression)
	source_motion_points = scale * (motion_points @ rotation.T + source_expression) + translation
	target_motion_points = scale * (motion_points @ rotation.T + target_expression) + translation
	crop_vision_frame = forward_generate_frame(feature_volume, source_motion_points, target_motion_points)
	return crop_vision_frame


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


def forward_generate_frame(feature_volume : LivePortraitFeatureVolume, source_motion_points : LivePortraitMotionPoints, target_motion_points : LivePortraitMotionPoints) -> VisionFrame:
	generator = get_inference_pool().get('generator')

	with thread_semaphore():
		crop_vision_frame = generator.run(None,
		{
			'feature_volume': feature_volume,
			'source': source_motion_points,
			'target': target_motion_points
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


def get_reference_frame(source_face : Face, target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	pass


def process_frame(inputs : ExpressionRestorerInputs) -> VisionFrame:
	reference_faces = inputs.get('reference_faces')
	source_vision_frame = inputs.get('source_vision_frame')
	target_vision_frame = inputs.get('target_vision_frame')
	many_faces = sort_and_filter_faces(get_many_faces([ target_vision_frame ]))

	if state_manager.get_item('face_selector_mode') == 'many':
		if many_faces:
			for target_face in many_faces:
				target_vision_frame = restore_expression(source_vision_frame, target_face, target_vision_frame)
	if state_manager.get_item('face_selector_mode') == 'one':
		target_face = get_one_face(many_faces)
		if target_face:
			target_vision_frame = restore_expression(source_vision_frame, target_face, target_vision_frame)
	if state_manager.get_item('face_selector_mode') == 'reference':
		similar_faces = find_similar_faces(many_faces, reference_faces, state_manager.get_item('reference_face_distance'))
		if similar_faces:
			for similar_face in similar_faces:
				target_vision_frame = restore_expression(source_vision_frame, similar_face, target_vision_frame)
	return target_vision_frame


def process_frames(source_path : List[str], queue_payloads : List[QueuePayload], update_progress : UpdateProgress) -> None:
	reference_faces = get_reference_faces() if 'reference' in state_manager.get_item('face_selector_mode') else None

	for queue_payload in process_manager.manage(queue_payloads):
		frame_number = queue_payload.get('frame_number')
		if state_manager.get_item('trim_frame_start'):
			frame_number += state_manager.get_item('trim_frame_start')
		source_vision_frame = read_video_frame(state_manager.get_item('target_path'), frame_number)
		target_vision_path = queue_payload.get('frame_path')
		target_vision_frame = read_image(target_vision_path)
		output_vision_frame = process_frame(
		{
			'reference_faces': reference_faces,
			'source_vision_frame': source_vision_frame,
			'target_vision_frame': target_vision_frame
		})
		write_image(target_vision_path, output_vision_frame)
		update_progress(1)


def process_image(source_path : str, target_path : str, output_path : str) -> None:
	reference_faces = get_reference_faces() if 'reference' in state_manager.get_item('face_selector_mode') else None
	source_vision_frame = read_static_image(state_manager.get_item('target_path'))
	target_vision_frame = read_static_image(target_path)
	output_vision_frame = process_frame(
	{
		'reference_faces': reference_faces,
		'source_vision_frame': source_vision_frame,
		'target_vision_frame': target_vision_frame
	})
	write_image(output_path, output_vision_frame)


def process_video(source_paths : List[str], temp_frame_paths : List[str]) -> None:
	processors.multi_process_frames(None, temp_frame_paths, process_frames)
