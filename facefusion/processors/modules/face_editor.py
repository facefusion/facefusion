from argparse import ArgumentParser
from time import sleep
from typing import Any, List, Optional

import cv2
import numpy
from numpy.typing import NDArray

import facefusion.jobs.job_manager
import facefusion.jobs.job_store
import facefusion.processors.core as processors
from facefusion import config, content_analyser, face_analyser, face_masker, logger, process_manager, state_manager, wording
from facefusion.common_helper import create_metavar
from facefusion.download import conditional_download_hashes, conditional_download_sources
from facefusion.execution import create_inference_pool
from facefusion.face_analyser import get_many_faces, get_one_face
from facefusion.face_helper import paste_back, warp_face_by_face_landmark_5
from facefusion.face_masker import create_occlusion_mask, create_static_box_mask
from facefusion.face_selector import find_similar_faces, sort_and_filter_faces
from facefusion.face_store import get_reference_faces
from facefusion.filesystem import in_directory, is_image, is_video, resolve_relative_path, same_file_extension
from facefusion.processors import choices as processors_choices
from facefusion.processors.typing import FaceEditorInputs
from facefusion.program_helper import find_argument_group
from facefusion.thread_helper import thread_lock, thread_semaphore
from facefusion.typing import Args, Face, FaceLandmark68, InferencePool, ModelOptions, ModelSet, ProcessMode, QueuePayload, UpdateProgress, VisionFrame
from facefusion.vision import read_image, read_static_image, write_image

INFERENCE_POOL : Optional[InferencePool] = None
NAME = __name__.upper()
MODEL_SET : ModelSet =\
{
	'live_portrait':
	{
		'hashes':
		{
			'feature_extractor':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/live_portrait_feature_extractor.hash',
				'path': resolve_relative_path('../.assets/models/live_portrait_feature_extractor.hash')
			},
			'motion_extractor':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/live_portrait_motion_extractor.hash',
				'path': resolve_relative_path('../.assets/models/live_portrait_motion_extractor.hash')
			},
			'eye_retargeter':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/live_portrait_eye_retargeter.hash',
				'path': resolve_relative_path('../.assets/models/live_portrait_eye_retargeter.hash')
			},
			'lip_retargeter':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/live_portrait_lip_retargeter.hash',
				'path': resolve_relative_path('../.assets/models/live_portrait_lip_retargeter.hash')
			},
			'generator':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/live_portrait_generator.hash',
				'path': resolve_relative_path('../.assets/models/live_portrait_generator.hash')
			}
		},
		'sources':
		{
			'feature_extractor':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/live_portrait_feature_extractor.onnx',
				'path': resolve_relative_path('../.assets/models/live_portrait_feature_extractor.onnx')
			},
			'motion_extractor':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/live_portrait_motion_extractor.onnx',
				'path': resolve_relative_path('../.assets/models/live_portrait_motion_extractor.onnx')
			},
			'eye_retargeter':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/live_portrait_eye_retargeter.onnx',
				'path': resolve_relative_path('../.assets/models/live_portrait_eye_retargeter.onnx')
			},
			'lip_retargeter':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/live_portrait_lip_retargeter.onnx',
				'path': resolve_relative_path('../.assets/models/live_portrait_lip_retargeter.onnx')
			},
			'generator':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/live_portrait_generator.onnx',
				'path': resolve_relative_path('../.assets/models/live_portrait_generator.onnx')
			}
		},
		'template': 'ffhq_512',
		'size': (512, 512)
	}
}


def get_inference_pool() -> InferencePool:
	global INFERENCE_POOL

	with thread_lock():
		while process_manager.is_checking():
			sleep(0.5)
		if INFERENCE_POOL is None:
			module_sources = get_model_options().get('sources')
			INFERENCE_POOL = create_inference_pool(module_sources, state_manager.get_item('execution_device_id'), state_manager.get_item('execution_providers'))
	return INFERENCE_POOL


def clear_inference_pool() -> None:
	global INFERENCE_POOL

	INFERENCE_POOL = None


def get_model_options() -> ModelOptions:
	return MODEL_SET[state_manager.get_item('face_editor_model')]


def register_args(program : ArgumentParser) -> None:
	group_processors = find_argument_group(program, 'processors')
	if group_processors:
		group_processors.add_argument('--face-editor-model', help = wording.get('help.face_editor_model'), default = config.get_str_value('processors.face_editor_model', 'live_portrait'), choices = processors_choices.face_editor_models)
		group_processors.add_argument('--face-editor-eye-open-ratio', help = wording.get('help.face_editor_eye_open_ratio'), type = float, default = config.get_float_value('processors.face_editor_eye_open_ratio', '0'), choices = processors_choices.face_editor_eye_open_ratio_range, metavar = create_metavar(processors_choices.face_editor_eye_open_ratio_range))
		group_processors.add_argument('--face-editor-lip-open-ratio', help = wording.get('help.face_editor_lip_open_ratio'), type = float, default = config.get_float_value('processors.face_editor_lip_open_ratio', '0'), choices = processors_choices.face_editor_lip_open_ratio_range, metavar = create_metavar(processors_choices.face_editor_lip_open_ratio_range))
		facefusion.jobs.job_store.register_step_keys([ 'face_editor_model','face_editor_eye_open_ratio', 'face_editor_lip_open_ratio' ])


def apply_args(args : Args) -> None:
	state_manager.init_item('face_editor_model', args.get('face_editor_model'))
	state_manager.init_item('face_editor_eye_open_ratio', args.get('face_editor_eye_open_ratio'))
	state_manager.init_item('face_editor_lip_open_ratio', args.get('face_editor_lip_open_ratio'))


def pre_check() -> bool:
	download_directory_path = resolve_relative_path('../.assets/models')
	model_hashes = get_model_options().get('hashes')
	model_sources = get_model_options().get('sources')

	return conditional_download_hashes(download_directory_path, model_hashes) and conditional_download_sources(download_directory_path, model_sources)


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
		clear_inference_pool()
	if state_manager.get_item('video_memory_strategy') == 'strict':
		content_analyser.clear_inference_pool()
		face_analyser.clear_inference_pool()
		face_masker.clear_inference_pool()


def edit_face(target_face: Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	model_template = get_model_options().get('template')
	model_size = get_model_options().get('size')
	face_landmark_5 = target_face.landmark_set.get('5/68')
	face_landmark_5 = (face_landmark_5 - face_landmark_5[2]) * 1.2 + face_landmark_5[2]
	crop_vision_frame, affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, face_landmark_5, model_template, model_size)
	box_mask = create_static_box_mask(crop_vision_frame.shape[:2][::-1], state_manager.get_item('face_mask_blur'), (0, 0, 0, 0))
	crop_masks =\
	[
		box_mask
	]

	if 'occlusion' in state_manager.get_item('face_mask_types'):
		occlusion_mask = create_occlusion_mask(crop_vision_frame)
		crop_masks.append(occlusion_mask)
	crop_vision_frame = prepare_crop_frame(crop_vision_frame)
	crop_vision_frame = apply_edit_face(crop_vision_frame, target_face.landmark_set.get('68'))
	crop_vision_frame = normalize_crop_frame(crop_vision_frame)
	crop_mask = numpy.minimum.reduce(crop_masks).clip(0, 1)
	temp_vision_frame = paste_back(temp_vision_frame, crop_vision_frame, crop_mask, affine_matrix)
	return temp_vision_frame


def apply_edit_face(crop_vision_frame : VisionFrame, face_landmark_68 : FaceLandmark68) -> VisionFrame:
	feature_extractor = get_inference_pool().get('feature_extractor')
	motion_extractor = get_inference_pool().get('motion_extractor')
	generator = get_inference_pool().get('generator')

	with thread_semaphore():
		feature_volume = feature_extractor.run(None,
		{
			'input': crop_vision_frame
		})[0]

	with thread_semaphore():
		motion_points = motion_extractor.run(None,
		{
			'input': crop_vision_frame
		})[5]
	eye_motion_points = edit_eye_motion_points(motion_points, face_landmark_68)
	lip_motion_points = edit_lip_motion_points(motion_points, face_landmark_68)
	motion_points_edit = motion_points + eye_motion_points + lip_motion_points

	with thread_semaphore():
		crop_vision_frame = generator.run(None,
		{
			'feature_volume': feature_volume,
			'target': motion_points,
			'source': motion_points_edit
		})[0][0]
	return crop_vision_frame


def edit_eye_motion_points(motion_points : NDArray[Any], face_landmark_68 : FaceLandmark68) -> NDArray[Any]:
	eye_retargeter = get_inference_pool().get('eye_retargeter')
	face_editor_eye_open_ratio = state_manager.get_item('face_editor_eye_open_ratio')
	left_eye_ratio = calc_distance_ratio(face_landmark_68, 37, 40, 39, 36)
	right_eye_ratio = calc_distance_ratio(face_landmark_68, 43, 46, 45, 42)

	if face_editor_eye_open_ratio < 0:
		close_eye_ratio = numpy.array([ left_eye_ratio, right_eye_ratio, 0 ]).astype(numpy.float32).reshape(1, -1)

		with thread_semaphore():
			close_eye_motion_points = eye_retargeter.run(None,
			{
				'input': numpy.concatenate([ motion_points.reshape(1, -1), close_eye_ratio ], axis = 1)
			})[0]
		eye_motion_points = close_eye_motion_points * face_editor_eye_open_ratio * -1
	else:
		open_eye_ratio = numpy.array([ left_eye_ratio, right_eye_ratio, 0.8 ]).astype(numpy.float32).reshape(1, -1)

		with thread_semaphore():
			open_eye_motion_points = eye_retargeter.run(None,
			{
				'input': numpy.concatenate([ motion_points.reshape(1, -1), open_eye_ratio ], axis = 1)
			})[0]
		eye_motion_points = open_eye_motion_points * face_editor_eye_open_ratio
	eye_motion_points = eye_motion_points.reshape(-1, 21, 3)
	return eye_motion_points


def edit_lip_motion_points(motion_points : NDArray[Any], face_landmark_68 : FaceLandmark68) -> NDArray[Any]:
	lip_retargeter = get_inference_pool().get('lip_retargeter')
	face_editor_lip_open_ratio = state_manager.get_item('face_editor_lip_open_ratio')
	lip_ratio = calc_distance_ratio(face_landmark_68, 62, 66, 54, 48)

	if face_editor_lip_open_ratio < 0:
		close_lip_ratio = numpy.array([ lip_ratio, 0 ]).astype(numpy.float32).reshape(1, -1)

		with thread_semaphore():
			close_lip_motion_points = lip_retargeter.run(None,
			{
				'input': numpy.concatenate([ motion_points.reshape(1, -1), close_lip_ratio ], axis = 1)
			})[0]
		lip_motion_points = close_lip_motion_points * face_editor_lip_open_ratio * -1
	else:
		open_lip_ratio = numpy.array([ lip_ratio, 1.3 ]).astype(numpy.float32).reshape(1, -1)

		with thread_semaphore():
			open_lip_motion_points = lip_retargeter.run(None,
			{
				'input': numpy.concatenate([ motion_points.reshape(1, -1), open_lip_ratio ], axis = 1)
			})[0]
		lip_motion_points = open_lip_motion_points * face_editor_lip_open_ratio
	lip_motion_points = lip_motion_points.reshape(-1, 21, 3)
	return lip_motion_points


def calc_distance_ratio(face_landmark_68 : FaceLandmark68, top_index : int, bottom_index : int, left_index : int, right_index : int) -> float:
	vertical_direction = face_landmark_68[top_index] - face_landmark_68[bottom_index]
	horizontal_direction = face_landmark_68[left_index] - face_landmark_68[right_index]
	distance_ratio = float(numpy.linalg.norm(vertical_direction) / (numpy.linalg.norm(horizontal_direction) + 1e-6))
	return distance_ratio


def prepare_crop_frame(crop_vision_frame : VisionFrame) -> VisionFrame:
	crop_vision_frame = cv2.resize(crop_vision_frame, (256, 256), interpolation = cv2.INTER_AREA)
	crop_vision_frame = crop_vision_frame[:, :, ::-1] / 255.0
	crop_vision_frame = numpy.expand_dims(crop_vision_frame.transpose(2, 0, 1), axis = 0).astype(numpy.float32)
	return crop_vision_frame


def normalize_crop_frame(crop_vision_frame : VisionFrame) -> VisionFrame:
	crop_vision_frame = crop_vision_frame.transpose(1, 2, 0).clip(0, 1)
	crop_vision_frame = (crop_vision_frame * 255.0)
	crop_vision_frame = crop_vision_frame.astype(numpy.uint8)[:, :, ::-1]
	return crop_vision_frame


def get_reference_frame(source_face : Face, target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	pass


def process_frame(inputs : FaceEditorInputs) -> VisionFrame:
	reference_faces = inputs.get('reference_faces')
	target_vision_frame = inputs.get('target_vision_frame')
	many_faces = sort_and_filter_faces(get_many_faces([ target_vision_frame ]))

	if state_manager.get_item('face_selector_mode') == 'many':
		if many_faces:
			for target_face in many_faces:
				target_vision_frame = edit_face(target_face, target_vision_frame)
	if state_manager.get_item('face_selector_mode') == 'one':
		target_face = get_one_face(many_faces)
		if target_face:
			target_vision_frame = edit_face(target_face, target_vision_frame)
	if state_manager.get_item('face_selector_mode') == 'reference':
		similar_faces = find_similar_faces(many_faces, reference_faces, state_manager.get_item('reference_face_distance'))
		if similar_faces:
			for similar_face in similar_faces:
				target_vision_frame = edit_face(similar_face, target_vision_frame)
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
	processors.multi_process_frames(None, temp_frame_paths, process_frames)
