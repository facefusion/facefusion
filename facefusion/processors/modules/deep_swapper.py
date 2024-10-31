from argparse import ArgumentParser
from typing import List, Tuple

import cv2
import numpy

import facefusion.jobs.job_manager
import facefusion.jobs.job_store
import facefusion.processors.core as processors
from facefusion import config, content_analyser, face_classifier, face_detector, face_landmarker, face_masker, face_recognizer, inference_manager, logger, process_manager, state_manager, wording
from facefusion.download import conditional_download_hashes, conditional_download_sources
from facefusion.face_analyser import get_many_faces, get_one_face
from facefusion.face_helper import paste_back, warp_face_by_face_landmark_5
from facefusion.face_masker import create_occlusion_mask, create_static_box_mask
from facefusion.face_selector import find_similar_faces, sort_and_filter_faces
from facefusion.face_store import get_reference_faces
from facefusion.filesystem import in_directory, is_image, is_video, resolve_relative_path, same_file_extension
from facefusion.processors import choices as processors_choices
from facefusion.processors.typing import DeepSwapperInputs
from facefusion.program_helper import find_argument_group
from facefusion.thread_helper import thread_semaphore
from facefusion.typing import ApplyStateItem, Args, Face, InferencePool, Mask, ModelOptions, ModelSet, ProcessMode, QueuePayload, UpdateProgress, VisionFrame
from facefusion.vision import read_image, read_static_image, write_image

MODEL_SET : ModelSet =\
{
	'jackie_chan':
	{
		'hashes':
		{
			'deep_swapper':
			{
				'url': 'https://huggingface.co/bluefoxcreation/DFM/resolve/main/Jackie_Chan.hash',
				'path': resolve_relative_path('../.assets/models/Jackie_Chan.hash')
			}
		},
		'sources':
		{
			'deep_swapper':
			{
				'url': 'https://github.com/iperov/DeepFaceLive/releases/download/JACKIE_CHAN/Jackie_Chan.dfm',
				'path': resolve_relative_path('../.assets/models/Jackie_Chan.dfm')
			}
		},
		'template': 'arcface_128_v2',
		'size': (224, 224)
	}
}


def get_inference_pool() -> InferencePool:
	model_sources = get_model_options().get('sources')
	model_context = __name__ + '.' + state_manager.get_item('deep_swapper_model')
	return inference_manager.get_inference_pool(model_context, model_sources)


def clear_inference_pool() -> None:
	model_context = __name__ + '.' + state_manager.get_item('deep_swapper_model')
	inference_manager.clear_inference_pool(model_context)


def get_model_options() -> ModelOptions:
	deep_swapper_model = state_manager.get_item('deep_swapper_model')
	return MODEL_SET.get(deep_swapper_model)


def register_args(program : ArgumentParser) -> None:
	group_processors = find_argument_group(program, 'processors')
	if group_processors:
		group_processors.add_argument('--deep-swapper-model', help = wording.get('help.deep_swapper_model'), default = config.get_str_value('processors.deep_swapper_model', 'jackie_chan'), choices = processors_choices.deep_swapper_models)
		facefusion.jobs.job_store.register_step_keys([ 'deep_swapper_model' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('deep_swapper_model', args.get('deep_swapper_model'))


def pre_check() -> bool:
	download_directory_path = resolve_relative_path('../.assets/models')
	model_hashes = get_model_options().get('hashes')
	model_sources = get_model_options().get('sources')

	return conditional_download_hashes(download_directory_path, model_hashes) and conditional_download_sources(download_directory_path, model_sources)


def pre_process(mode : ProcessMode) -> bool:
	if mode in [ 'output', 'preview' ] and not is_image(state_manager.get_item('target_path')) and not is_video(state_manager.get_item('target_path')):
		logger.error(wording.get('choose_image_or_video_target') + wording.get('exclamation_mark'), __name__)
		return False
	if mode == 'output' and not in_directory(state_manager.get_item('output_path')):
		logger.error(wording.get('specify_image_or_video_output') + wording.get('exclamation_mark'), __name__)
		return False
	if mode == 'output' and not same_file_extension([ state_manager.get_item('target_path'), state_manager.get_item('output_path') ]):
		logger.error(wording.get('match_target_and_output_extension') + wording.get('exclamation_mark'), __name__)
		return False
	return True


def post_process() -> None:
	read_static_image.cache_clear()
	if state_manager.get_item('video_memory_strategy') in [ 'strict', 'moderate' ]:
		clear_inference_pool()
	if state_manager.get_item('video_memory_strategy') == 'strict':
		content_analyser.clear_inference_pool()
		face_classifier.clear_inference_pool()
		face_detector.clear_inference_pool()
		face_landmarker.clear_inference_pool()
		face_masker.clear_inference_pool()
		face_recognizer.clear_inference_pool()


def swap_face(target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	model_template = get_model_options().get('template')
	model_size = get_model_options().get('size')
	crop_vision_frame, affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, target_face.landmark_set.get('5/68'), model_template, model_size)
	crop_vision_frame_raw = crop_vision_frame.copy()
	box_mask = create_static_box_mask(crop_vision_frame.shape[:2][::-1], state_manager.get_item('face_mask_blur'), state_manager.get_item('face_mask_padding'))
	crop_masks =\
	[
		box_mask
	]

	if 'occlusion' in state_manager.get_item('face_mask_types'):
		occlusion_mask = create_occlusion_mask(crop_vision_frame)
		crop_masks.append(occlusion_mask)

	crop_vision_frame = prepare_crop_frame(crop_vision_frame)
	crop_vision_frame, crop_source_mask, crop_target_mask = forward(crop_vision_frame)
	crop_vision_frame = normalize_crop_frame(crop_vision_frame)
	crop_vision_frame = match_frame_color_with_mask(crop_vision_frame_raw, crop_vision_frame, crop_source_mask, crop_target_mask)
	crop_masks.append(feather_crop_mask(crop_source_mask))
	crop_masks.append(feather_crop_mask(crop_target_mask))
	crop_mask = numpy.minimum.reduce(crop_masks).clip(0, 1)
	paste_vision_frame = paste_back(temp_vision_frame, crop_vision_frame, crop_mask, affine_matrix)
	return paste_vision_frame


def forward(crop_vision_frame : VisionFrame) -> Tuple[VisionFrame, Mask, Mask]:
	deep_swapper = get_inference_pool().get('deep_swapper')
	deep_swapper_inputs = {}

	for deep_swapper_input in deep_swapper.get_inputs():
		if deep_swapper_input.name == 'in_face:0':
			deep_swapper_inputs[deep_swapper_input.name] = crop_vision_frame
		if deep_swapper_input.name == 'morph_value:0':
			morph_value = numpy.array([ 1 ]).astype(numpy.float32)
			deep_swapper_inputs[deep_swapper_input.name] = morph_value

	with thread_semaphore():
		crop_target_mask, crop_vision_frame, crop_source_mask = deep_swapper.run(None, deep_swapper_inputs)

	return crop_vision_frame[0], crop_source_mask[0], crop_target_mask[0]


def prepare_crop_frame(crop_vision_frame : VisionFrame) -> VisionFrame:
	crop_vision_frame = cv2.addWeighted(crop_vision_frame, 1.5, cv2.GaussianBlur(crop_vision_frame, (0, 0), 2), -0.5, 0)
	crop_vision_frame = crop_vision_frame / 255.0
	crop_vision_frame = numpy.expand_dims(crop_vision_frame, axis = 0).astype(numpy.float32)
	return crop_vision_frame


def normalize_crop_frame(crop_vision_frame : VisionFrame) -> VisionFrame:
	crop_vision_frame = (crop_vision_frame * 255.0).clip(0, 255)
	crop_vision_frame = crop_vision_frame.astype(numpy.uint8)
	return crop_vision_frame


def feather_crop_mask(crop_source_mask : Mask) -> Mask:
	model_size = get_model_options().get('size')
	crop_mask = crop_source_mask.reshape(model_size).clip(0, 1)
	crop_mask = cv2.erode(crop_mask, numpy.ones((7, 7), numpy.uint8), iterations = 1)
	crop_mask = cv2.GaussianBlur(crop_mask, (15, 15), 0)
	return crop_mask


def match_frame_color_with_mask(source_vision_frame : VisionFrame, target_vision_frame : VisionFrame, source_mask : Mask, target_mask : Mask) -> VisionFrame:
	target_lab_frame = cv2.cvtColor(target_vision_frame, cv2.COLOR_BGR2LAB).astype(numpy.float32) / 255
	source_lab_frame = cv2.cvtColor(source_vision_frame, cv2.COLOR_BGR2LAB).astype(numpy.float32) / 255
	source_mask = (source_mask > 0.5).astype(numpy.float32)
	target_mask = (target_mask > 0.5).astype(numpy.float32)
	target_lab_filter = target_lab_frame * cv2.cvtColor(source_mask, cv2.COLOR_GRAY2BGR)
	source_lab_filter = source_lab_frame * cv2.cvtColor(target_mask, cv2.COLOR_GRAY2BGR)
	target_lab_frame -= target_lab_filter.mean(axis = ( 0, 1 ))
	target_lab_frame /= target_lab_filter.std(axis = ( 0, 1 )) + 1e-6
	target_lab_frame *= source_lab_filter.std(axis = ( 0, 1 ))
	target_lab_frame += source_lab_filter.mean(axis = ( 0, 1 ))
	target_lab_frame = numpy.multiply(target_lab_frame.clip(0, 1), 255).astype(numpy.uint8)
	target_vision_frame = cv2.cvtColor(target_lab_frame, cv2.COLOR_LAB2BGR)
	return target_vision_frame


def get_reference_frame(source_face : Face, target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	return swap_face(target_face, temp_vision_frame)


def process_frame(inputs : DeepSwapperInputs) -> VisionFrame:
	reference_faces = inputs.get('reference_faces')
	target_vision_frame = inputs.get('target_vision_frame')
	many_faces = sort_and_filter_faces(get_many_faces([ target_vision_frame ]))

	if state_manager.get_item('face_selector_mode') == 'many':
		if many_faces:
			for target_face in many_faces:
				target_vision_frame = swap_face(target_face, target_vision_frame)
	if state_manager.get_item('face_selector_mode') == 'one':
		target_face = get_one_face(many_faces)
		if target_face:
			target_vision_frame = swap_face(target_face, target_vision_frame)
	if state_manager.get_item('face_selector_mode') == 'reference':
		similar_faces = find_similar_faces(many_faces, reference_faces, state_manager.get_item('reference_face_distance'))
		if similar_faces:
			for similar_face in similar_faces:
				target_vision_frame = swap_face(similar_face, target_vision_frame)
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