from argparse import ArgumentParser
from typing import List

import cv2
import numpy

import facefusion.jobs.job_manager
import facefusion.jobs.job_store
import facefusion.processors.core as processors
from facefusion import config, content_analyser, face_classifier, face_detector, face_landmarker, face_masker, face_recognizer, logger, process_manager, state_manager, video_manager, wording
from facefusion.face_analyser import get_many_faces, get_one_face
from facefusion.face_helper import warp_face_by_face_landmark_5
from facefusion.face_masker import create_area_mask, create_box_mask, create_occlusion_mask, create_region_mask
from facefusion.face_selector import find_similar_faces, sort_and_filter_faces
from facefusion.face_store import get_reference_faces
from facefusion.filesystem import in_directory, same_file_extension
from facefusion.processors import choices as processors_choices
from facefusion.processors.types import FaceDebuggerInputs
from facefusion.program_helper import find_argument_group
from facefusion.types import ApplyStateItem, Args, Face, InferencePool, ProcessMode, QueuePayload, UpdateProgress, VisionFrame
from facefusion.vision import read_image, read_static_image, write_image


def get_inference_pool() -> InferencePool:
	pass


def clear_inference_pool() -> None:
	pass


def register_args(program : ArgumentParser) -> None:
	group_processors = find_argument_group(program, 'processors')
	if group_processors:
		group_processors.add_argument('--face-debugger-items', help = wording.get('help.face_debugger_items').format(choices = ', '.join(processors_choices.face_debugger_items)), default = config.get_str_list('processors', 'face_debugger_items', 'face-landmark-5/68 face-mask'), choices = processors_choices.face_debugger_items, nargs = '+', metavar = 'FACE_DEBUGGER_ITEMS')
		facefusion.jobs.job_store.register_step_keys([ 'face_debugger_items' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('face_debugger_items', args.get('face_debugger_items'))


def pre_check() -> bool:
	return True


def pre_process(mode : ProcessMode) -> bool:
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
	if state_manager.get_item('video_memory_strategy') == 'strict':
		content_analyser.clear_inference_pool()
		face_classifier.clear_inference_pool()
		face_detector.clear_inference_pool()
		face_landmarker.clear_inference_pool()
		face_masker.clear_inference_pool()
		face_recognizer.clear_inference_pool()


def debug_face(target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	primary_color = (0, 0, 255)
	primary_light_color = (100, 100, 255)
	secondary_color = (0, 255, 0)
	tertiary_color = (255, 255, 0)
	bounding_box = target_face.bounding_box.astype(numpy.int32)
	temp_vision_frame = temp_vision_frame.copy()
	has_face_landmark_5_fallback = numpy.array_equal(target_face.landmark_set.get('5'), target_face.landmark_set.get('5/68'))
	has_face_landmark_68_fallback = numpy.array_equal(target_face.landmark_set.get('68'), target_face.landmark_set.get('68/5'))
	face_debugger_items = state_manager.get_item('face_debugger_items')

	if 'bounding-box' in face_debugger_items:
		x1, y1, x2, y2 = bounding_box
		cv2.rectangle(temp_vision_frame, (x1, y1), (x2, y2), primary_color, 2)

		if target_face.angle == 0:
			cv2.line(temp_vision_frame, (x1, y1), (x2, y1), primary_light_color, 3)
		if target_face.angle == 180:
			cv2.line(temp_vision_frame, (x1, y2), (x2, y2), primary_light_color, 3)
		if target_face.angle == 90:
			cv2.line(temp_vision_frame, (x2, y1), (x2, y2), primary_light_color, 3)
		if target_face.angle == 270:
			cv2.line(temp_vision_frame, (x1, y1), (x1, y2), primary_light_color, 3)

	if 'face-mask' in face_debugger_items:
		crop_vision_frame, affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, target_face.landmark_set.get('5/68'), 'arcface_128', (512, 512))
		inverse_matrix = cv2.invertAffineTransform(affine_matrix)
		temp_size = temp_vision_frame.shape[:2][::-1]
		crop_masks = []

		if 'box' in state_manager.get_item('face_mask_types'):
			box_mask = create_box_mask(crop_vision_frame, 0, state_manager.get_item('face_mask_padding'))
			crop_masks.append(box_mask)

		if 'occlusion' in state_manager.get_item('face_mask_types'):
			occlusion_mask = create_occlusion_mask(crop_vision_frame)
			crop_masks.append(occlusion_mask)

		if 'area' in state_manager.get_item('face_mask_types'):
			face_landmark_68 = cv2.transform(target_face.landmark_set.get('68').reshape(1, -1, 2), affine_matrix).reshape(-1, 2)
			area_mask = create_area_mask(crop_vision_frame, face_landmark_68, state_manager.get_item('face_mask_areas'))
			crop_masks.append(area_mask)

		if 'region' in state_manager.get_item('face_mask_types'):
			region_mask = create_region_mask(crop_vision_frame, state_manager.get_item('face_mask_regions'))
			crop_masks.append(region_mask)

		crop_mask = numpy.minimum.reduce(crop_masks).clip(0, 1)
		crop_mask = (crop_mask * 255).astype(numpy.uint8)
		inverse_vision_frame = cv2.warpAffine(crop_mask, inverse_matrix, temp_size)
		inverse_vision_frame = cv2.threshold(inverse_vision_frame, 100, 255, cv2.THRESH_BINARY)[1]
		inverse_vision_frame[inverse_vision_frame > 0] = 255 #type:ignore[operator]
		inverse_contours = cv2.findContours(inverse_vision_frame, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)[0]
		cv2.drawContours(temp_vision_frame, inverse_contours, -1, tertiary_color if has_face_landmark_5_fallback else secondary_color, 2)

	if 'face-landmark-5' in face_debugger_items and numpy.any(target_face.landmark_set.get('5')):
		face_landmark_5 = target_face.landmark_set.get('5').astype(numpy.int32)
		for index in range(face_landmark_5.shape[0]):
			cv2.circle(temp_vision_frame, (face_landmark_5[index][0], face_landmark_5[index][1]), 3, primary_color, -1)

	if 'face-landmark-5/68' in face_debugger_items and numpy.any(target_face.landmark_set.get('5/68')):
		face_landmark_5_68 = target_face.landmark_set.get('5/68').astype(numpy.int32)
		for index in range(face_landmark_5_68.shape[0]):
			cv2.circle(temp_vision_frame, (face_landmark_5_68[index][0], face_landmark_5_68[index][1]), 3, tertiary_color if has_face_landmark_5_fallback else secondary_color, -1)

	if 'face-landmark-68' in face_debugger_items and numpy.any(target_face.landmark_set.get('68')):
		face_landmark_68 = target_face.landmark_set.get('68').astype(numpy.int32)
		for index in range(face_landmark_68.shape[0]):
			cv2.circle(temp_vision_frame, (face_landmark_68[index][0], face_landmark_68[index][1]), 3, tertiary_color if has_face_landmark_68_fallback else secondary_color, -1)

	if 'face-landmark-68/5' in face_debugger_items and numpy.any(target_face.landmark_set.get('68')):
		face_landmark_68 = target_face.landmark_set.get('68/5').astype(numpy.int32)
		for index in range(face_landmark_68.shape[0]):
			cv2.circle(temp_vision_frame, (face_landmark_68[index][0], face_landmark_68[index][1]), 3, tertiary_color, -1)

	if bounding_box[3] - bounding_box[1] > 50 and bounding_box[2] - bounding_box[0] > 50:
		top = bounding_box[1]
		left = bounding_box[0] - 20

		if 'face-detector-score' in face_debugger_items:
			face_score_text = str(round(target_face.score_set.get('detector'), 2))
			top = top + 20
			cv2.putText(temp_vision_frame, face_score_text, (left, top), cv2.FONT_HERSHEY_SIMPLEX, 0.5, primary_color, 2)

		if 'face-landmarker-score' in face_debugger_items:
			face_score_text = str(round(target_face.score_set.get('landmarker'), 2))
			top = top + 20
			cv2.putText(temp_vision_frame, face_score_text, (left, top), cv2.FONT_HERSHEY_SIMPLEX, 0.5, tertiary_color if has_face_landmark_5_fallback else secondary_color, 2)

		if 'age' in face_debugger_items:
			face_age_text = str(target_face.age.start) + '-' + str(target_face.age.stop)
			top = top + 20
			cv2.putText(temp_vision_frame, face_age_text, (left, top), cv2.FONT_HERSHEY_SIMPLEX, 0.5, primary_color, 2)

		if 'gender' in face_debugger_items:
			face_gender_text = target_face.gender
			top = top + 20
			cv2.putText(temp_vision_frame, face_gender_text, (left, top), cv2.FONT_HERSHEY_SIMPLEX, 0.5, primary_color, 2)

		if 'race' in face_debugger_items:
			face_race_text = target_face.race
			top = top + 20
			cv2.putText(temp_vision_frame, face_race_text, (left, top), cv2.FONT_HERSHEY_SIMPLEX, 0.5, primary_color, 2)

	return temp_vision_frame


def get_reference_frame(source_face : Face, target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	pass


def process_frame(inputs : FaceDebuggerInputs) -> VisionFrame:
	reference_faces = inputs.get('reference_faces')
	target_vision_frame = inputs.get('target_vision_frame')
	many_faces = sort_and_filter_faces(get_many_faces([ target_vision_frame ]))

	if state_manager.get_item('face_selector_mode') == 'many':
		if many_faces:
			for target_face in many_faces:
				target_vision_frame = debug_face(target_face, target_vision_frame)
	if state_manager.get_item('face_selector_mode') == 'one':
		target_face = get_one_face(many_faces)
		if target_face:
			target_vision_frame = debug_face(target_face, target_vision_frame)
	if state_manager.get_item('face_selector_mode') == 'reference':
		similar_faces = find_similar_faces(many_faces, reference_faces, state_manager.get_item('reference_face_distance'))
		if similar_faces:
			for similar_face in similar_faces:
				target_vision_frame = debug_face(similar_face, target_vision_frame)
	return target_vision_frame


def process_frames(source_paths : List[str], queue_payloads : List[QueuePayload], update_progress : UpdateProgress) -> None:
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


def process_image(source_paths : List[str], target_path : str, output_path : str) -> None:
	reference_faces = get_reference_faces() if 'reference' in state_manager.get_item('face_selector_mode') else None
	target_vision_frame = read_static_image(target_path)
	output_vision_frame = process_frame(
	{
		'reference_faces': reference_faces,
		'target_vision_frame': target_vision_frame
	})
	write_image(output_path, output_vision_frame)


def process_video(source_paths : List[str], temp_frame_paths : List[str]) -> None:
	processors.multi_process_frames(source_paths, temp_frame_paths, process_frames)
