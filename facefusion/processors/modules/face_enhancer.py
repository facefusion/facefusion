from argparse import ArgumentParser
from functools import lru_cache
from typing import List

import cv2
import numpy

import facefusion.jobs.job_manager
import facefusion.jobs.job_store
import facefusion.processors.core as processors
from facefusion import config, content_analyser, face_classifier, face_detector, face_landmarker, face_masker, face_recognizer, inference_manager, logger, process_manager, state_manager, video_manager, wording
from facefusion.common_helper import create_float_metavar, create_int_metavar
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.face_analyser import get_many_faces, get_one_face
from facefusion.face_helper import paste_back, warp_face_by_face_landmark_5
from facefusion.face_masker import create_box_mask, create_occlusion_mask
from facefusion.face_selector import find_similar_faces, sort_and_filter_faces
from facefusion.face_store import get_reference_faces
from facefusion.filesystem import in_directory, is_image, is_video, resolve_relative_path, same_file_extension
from facefusion.processors import choices as processors_choices
from facefusion.processors.types import FaceEnhancerInputs, FaceEnhancerWeight
from facefusion.program_helper import find_argument_group
from facefusion.thread_helper import thread_semaphore
from facefusion.types import ApplyStateItem, Args, DownloadScope, Face, InferencePool, ModelOptions, ModelSet, ProcessMode, QueuePayload, UpdateProgress, VisionFrame
from facefusion.vision import read_image, read_static_image, write_image


@lru_cache(maxsize = None)
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
	return\
	{
		'codeformer':
		{
			'hashes':
			{
				'face_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'codeformer.hash'),
					'path': resolve_relative_path('../.assets/models/codeformer.hash')
				}
			},
			'sources':
			{
				'face_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'codeformer.onnx'),
					'path': resolve_relative_path('../.assets/models/codeformer.onnx')
				}
			},
			'template': 'ffhq_512',
			'size': (512, 512)
		},
		'gfpgan_1.2':
		{
			'hashes':
			{
				'face_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'gfpgan_1.2.hash'),
					'path': resolve_relative_path('../.assets/models/gfpgan_1.2.hash')
				}
			},
			'sources':
			{
				'face_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'gfpgan_1.2.onnx'),
					'path': resolve_relative_path('../.assets/models/gfpgan_1.2.onnx')
				}
			},
			'template': 'ffhq_512',
			'size': (512, 512)
		},
		'gfpgan_1.3':
		{
			'hashes':
			{
				'face_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'gfpgan_1.3.hash'),
					'path': resolve_relative_path('../.assets/models/gfpgan_1.3.hash')
				}
			},
			'sources':
			{
				'face_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'gfpgan_1.3.onnx'),
					'path': resolve_relative_path('../.assets/models/gfpgan_1.3.onnx')
				}
			},
			'template': 'ffhq_512',
			'size': (512, 512)
		},
		'gfpgan_1.4':
		{
			'hashes':
			{
				'face_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'gfpgan_1.4.hash'),
					'path': resolve_relative_path('../.assets/models/gfpgan_1.4.hash')
				}
			},
			'sources':
			{
				'face_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'gfpgan_1.4.onnx'),
					'path': resolve_relative_path('../.assets/models/gfpgan_1.4.onnx')
				}
			},
			'template': 'ffhq_512',
			'size': (512, 512)
		},
		'gpen_bfr_256':
		{
			'hashes':
			{
				'face_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'gpen_bfr_256.hash'),
					'path': resolve_relative_path('../.assets/models/gpen_bfr_256.hash')
				}
			},
			'sources':
			{
				'face_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'gpen_bfr_256.onnx'),
					'path': resolve_relative_path('../.assets/models/gpen_bfr_256.onnx')
				}
			},
			'template': 'arcface_128',
			'size': (256, 256)
		},
		'gpen_bfr_512':
		{
			'hashes':
			{
				'face_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'gpen_bfr_512.hash'),
					'path': resolve_relative_path('../.assets/models/gpen_bfr_512.hash')
				}
			},
			'sources':
			{
				'face_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'gpen_bfr_512.onnx'),
					'path': resolve_relative_path('../.assets/models/gpen_bfr_512.onnx')
				}
			},
			'template': 'ffhq_512',
			'size': (512, 512)
		},
		'gpen_bfr_1024':
		{
			'hashes':
			{
				'face_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'gpen_bfr_1024.hash'),
					'path': resolve_relative_path('../.assets/models/gpen_bfr_1024.hash')
				}
			},
			'sources':
			{
				'face_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'gpen_bfr_1024.onnx'),
					'path': resolve_relative_path('../.assets/models/gpen_bfr_1024.onnx')
				}
			},
			'template': 'ffhq_512',
			'size': (1024, 1024)
		},
		'gpen_bfr_2048':
		{
			'hashes':
			{
				'face_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'gpen_bfr_2048.hash'),
					'path': resolve_relative_path('../.assets/models/gpen_bfr_2048.hash')
				}
			},
			'sources':
			{
				'face_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'gpen_bfr_2048.onnx'),
					'path': resolve_relative_path('../.assets/models/gpen_bfr_2048.onnx')
				}
			},
			'template': 'ffhq_512',
			'size': (2048, 2048)
		},
		'restoreformer_plus_plus':
		{
			'hashes':
			{
				'face_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'restoreformer_plus_plus.hash'),
					'path': resolve_relative_path('../.assets/models/restoreformer_plus_plus.hash')
				}
			},
			'sources':
			{
				'face_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'restoreformer_plus_plus.onnx'),
					'path': resolve_relative_path('../.assets/models/restoreformer_plus_plus.onnx')
				}
			},
			'template': 'ffhq_512',
			'size': (512, 512)
		}
	}


def get_inference_pool() -> InferencePool:
	model_names = [ state_manager.get_item('face_enhancer_model') ]
	model_source_set = get_model_options().get('sources')

	return inference_manager.get_inference_pool(__name__, model_names, model_source_set)


def clear_inference_pool() -> None:
	model_names = [ state_manager.get_item('face_enhancer_model') ]
	inference_manager.clear_inference_pool(__name__, model_names)


def get_model_options() -> ModelOptions:
	model_name = state_manager.get_item('face_enhancer_model')
	return create_static_model_set('full').get(model_name)


def register_args(program : ArgumentParser) -> None:
	group_processors = find_argument_group(program, 'processors')
	if group_processors:
		group_processors.add_argument('--face-enhancer-model', help = wording.get('help.face_enhancer_model'), default = config.get_str_value('processors', 'face_enhancer_model', 'gfpgan_1.4'), choices = processors_choices.face_enhancer_models)
		group_processors.add_argument('--face-enhancer-blend', help = wording.get('help.face_enhancer_blend'), type = int, default = config.get_int_value('processors', 'face_enhancer_blend', '80'), choices = processors_choices.face_enhancer_blend_range, metavar = create_int_metavar(processors_choices.face_enhancer_blend_range))
		group_processors.add_argument('--face-enhancer-weight', help = wording.get('help.face_enhancer_weight'), type = float, default = config.get_float_value('processors', 'face_enhancer_weight', '1.0'), choices = processors_choices.face_enhancer_weight_range, metavar = create_float_metavar(processors_choices.face_enhancer_weight_range))
		facefusion.jobs.job_store.register_step_keys([ 'face_enhancer_model', 'face_enhancer_blend', 'face_enhancer_weight' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('face_enhancer_model', args.get('face_enhancer_model'))
	apply_state_item('face_enhancer_blend', args.get('face_enhancer_blend'))
	apply_state_item('face_enhancer_weight', args.get('face_enhancer_weight'))


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
		face_classifier.clear_inference_pool()
		face_detector.clear_inference_pool()
		face_landmarker.clear_inference_pool()
		face_masker.clear_inference_pool()
		face_recognizer.clear_inference_pool()


def enhance_face(target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	model_template = get_model_options().get('template')
	model_size = get_model_options().get('size')
	crop_vision_frame, affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, target_face.landmark_set.get('5/68'), model_template, model_size)
	box_mask = create_box_mask(crop_vision_frame, state_manager.get_item('face_mask_blur'), (0, 0, 0, 0))
	crop_masks =\
	[
		box_mask
	]

	if 'occlusion' in state_manager.get_item('face_mask_types'):
		occlusion_mask = create_occlusion_mask(crop_vision_frame)
		crop_masks.append(occlusion_mask)

	crop_vision_frame = prepare_crop_frame(crop_vision_frame)
	face_enhancer_weight = numpy.array([ state_manager.get_item('face_enhancer_weight') ]).astype(numpy.double)
	crop_vision_frame = forward(crop_vision_frame, face_enhancer_weight)
	crop_vision_frame = normalize_crop_frame(crop_vision_frame)
	crop_mask = numpy.minimum.reduce(crop_masks).clip(0, 1)
	paste_vision_frame = paste_back(temp_vision_frame, crop_vision_frame, crop_mask, affine_matrix)
	temp_vision_frame = blend_frame(temp_vision_frame, paste_vision_frame)
	return temp_vision_frame


def forward(crop_vision_frame : VisionFrame, face_enhancer_weight : FaceEnhancerWeight) -> VisionFrame:
	face_enhancer = get_inference_pool().get('face_enhancer')
	face_enhancer_inputs = {}

	for face_enhancer_input in face_enhancer.get_inputs():
		if face_enhancer_input.name == 'input':
			face_enhancer_inputs[face_enhancer_input.name] = crop_vision_frame
		if face_enhancer_input.name == 'weight':
			face_enhancer_inputs[face_enhancer_input.name] = face_enhancer_weight

	with thread_semaphore():
		crop_vision_frame = face_enhancer.run(None, face_enhancer_inputs)[0][0]

	return crop_vision_frame


def has_weight_input() -> bool:
	face_enhancer = get_inference_pool().get('face_enhancer')

	for deep_swapper_input in face_enhancer.get_inputs():
		if deep_swapper_input.name == 'weight':
			return True

	return False


def prepare_crop_frame(crop_vision_frame : VisionFrame) -> VisionFrame:
	crop_vision_frame = crop_vision_frame[:, :, ::-1] / 255.0
	crop_vision_frame = (crop_vision_frame - 0.5) / 0.5
	crop_vision_frame = numpy.expand_dims(crop_vision_frame.transpose(2, 0, 1), axis = 0).astype(numpy.float32)
	return crop_vision_frame


def normalize_crop_frame(crop_vision_frame : VisionFrame) -> VisionFrame:
	crop_vision_frame = numpy.clip(crop_vision_frame, -1, 1)
	crop_vision_frame = (crop_vision_frame + 1) / 2
	crop_vision_frame = crop_vision_frame.transpose(1, 2, 0)
	crop_vision_frame = (crop_vision_frame * 255.0).round()
	crop_vision_frame = crop_vision_frame.astype(numpy.uint8)[:, :, ::-1]
	return crop_vision_frame


def blend_frame(temp_vision_frame : VisionFrame, paste_vision_frame : VisionFrame) -> VisionFrame:
	face_enhancer_blend = 1 - (state_manager.get_item('face_enhancer_blend') / 100)
	temp_vision_frame = cv2.addWeighted(temp_vision_frame, face_enhancer_blend, paste_vision_frame, 1 - face_enhancer_blend, 0)
	return temp_vision_frame


def get_reference_frame(source_face : Face, target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	return enhance_face(target_face, temp_vision_frame)


def process_frame(inputs : FaceEnhancerInputs) -> VisionFrame:
	reference_faces = inputs.get('reference_faces')
	target_vision_frame = inputs.get('target_vision_frame')
	many_faces = sort_and_filter_faces(get_many_faces([ target_vision_frame ]))

	if state_manager.get_item('face_selector_mode') == 'many':
		if many_faces:
			for target_face in many_faces:
				target_vision_frame = enhance_face(target_face, target_vision_frame)
	if state_manager.get_item('face_selector_mode') == 'one':
		target_face = get_one_face(many_faces)
		if target_face:
			target_vision_frame = enhance_face(target_face, target_vision_frame)
	if state_manager.get_item('face_selector_mode') == 'reference':
		similar_faces = find_similar_faces(many_faces, reference_faces, state_manager.get_item('reference_face_distance'))
		if similar_faces:
			for similar_face in similar_faces:
				target_vision_frame = enhance_face(similar_face, target_vision_frame)
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
