from typing import Any, List, Literal
from argparse import ArgumentParser
import cv2
import numpy

import facefusion.globals
import facefusion.processors.frame.core as frame_processors
from facefusion import config, process_manager, wording
from facefusion.face_analyser import get_one_face, get_many_faces, find_similar_faces, clear_face_analyser
from facefusion.face_masker import create_static_box_mask, create_occlusion_mask, create_region_mask, clear_face_occluder, clear_face_parser
from facefusion.face_helper import warp_face_by_face_landmark_5, categorize_age, categorize_gender
from facefusion.face_store import get_reference_faces
from facefusion.content_analyser import clear_content_analyser
from facefusion.typing import Face, VisionFrame, UpdateProgress, ProcessMode, QueuePayload
from facefusion.vision import read_image, read_static_image, write_image
from facefusion.processors.frame.typings import FaceDebuggerInputs
from facefusion.processors.frame import globals as frame_processors_globals, choices as frame_processors_choices

NAME = __name__.upper()


def get_frame_processor() -> None:
	pass


def clear_frame_processor() -> None:
	pass


def get_options(key : Literal['model']) -> None:
	pass


def set_options(key : Literal['model'], value : Any) -> None:
	pass


def register_args(program : ArgumentParser) -> None:
	program.add_argument('--face-debugger-items', help = wording.get('help.face_debugger_items').format(choices = ', '.join(frame_processors_choices.face_debugger_items)), default = config.get_str_list('frame_processors.face_debugger_items', 'face-landmark-5/68 face-mask'), choices = frame_processors_choices.face_debugger_items, nargs = '+', metavar = 'FACE_DEBUGGER_ITEMS')


def apply_args(program : ArgumentParser) -> None:
	args = program.parse_args()
	frame_processors_globals.face_debugger_items = args.face_debugger_items


def pre_check() -> bool:
	return True


def post_check() -> bool:
	return True


def pre_process(mode : ProcessMode) -> bool:
	return True


def post_process() -> None:
	read_static_image.cache_clear()
	if facefusion.globals.video_memory_strategy == 'strict' or facefusion.globals.video_memory_strategy == 'moderate':
		clear_frame_processor()
	if facefusion.globals.video_memory_strategy == 'strict':
		clear_face_analyser()
		clear_content_analyser()
		clear_face_occluder()
		clear_face_parser()


def debug_face(target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	primary_color = (0, 0, 255)
	secondary_color = (0, 255, 0)
	tertiary_color = (255, 255, 0)
	bounding_box = target_face.bounding_box.astype(numpy.int32)
	temp_vision_frame = temp_vision_frame.copy()
	has_face_landmark_5_fallback = numpy.array_equal(target_face.landmarks.get('5'), target_face.landmarks.get('5/68'))
	has_face_landmark_68_fallback = numpy.array_equal(target_face.landmarks.get('68'), target_face.landmarks.get('68/5'))

	if 'bounding-box' in frame_processors_globals.face_debugger_items:
		cv2.rectangle(temp_vision_frame, (bounding_box[0], bounding_box[1]), (bounding_box[2], bounding_box[3]), primary_color, 2)
	if 'face-mask' in frame_processors_globals.face_debugger_items:
		crop_vision_frame, affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, target_face.landmarks.get('5/68'), 'arcface_128_v2', (512, 512))
		inverse_matrix = cv2.invertAffineTransform(affine_matrix)
		temp_size = temp_vision_frame.shape[:2][::-1]
		crop_mask_list = []
		if 'box' in facefusion.globals.face_mask_types:
			box_mask = create_static_box_mask(crop_vision_frame.shape[:2][::-1], 0, facefusion.globals.face_mask_padding)
			crop_mask_list.append(box_mask)
		if 'occlusion' in facefusion.globals.face_mask_types:
			occlusion_mask = create_occlusion_mask(crop_vision_frame)
			crop_mask_list.append(occlusion_mask)
		if 'region' in facefusion.globals.face_mask_types:
			region_mask = create_region_mask(crop_vision_frame, facefusion.globals.face_mask_regions)
			crop_mask_list.append(region_mask)
		crop_mask = numpy.minimum.reduce(crop_mask_list).clip(0, 1)
		crop_mask = (crop_mask * 255).astype(numpy.uint8)
		inverse_vision_frame = cv2.warpAffine(crop_mask, inverse_matrix, temp_size)
		inverse_vision_frame = cv2.threshold(inverse_vision_frame, 100, 255, cv2.THRESH_BINARY)[1]
		inverse_vision_frame[inverse_vision_frame > 0] = 255
		inverse_contours = cv2.findContours(inverse_vision_frame, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)[0]
		cv2.drawContours(temp_vision_frame, inverse_contours, -1, tertiary_color if has_face_landmark_5_fallback else secondary_color, 2)
	if 'face-landmark-5' in frame_processors_globals.face_debugger_items and numpy.any(target_face.landmarks.get('5')):
		face_landmark_5 = target_face.landmarks.get('5').astype(numpy.int32)
		for index in range(face_landmark_5.shape[0]):
			cv2.circle(temp_vision_frame, (face_landmark_5[index][0], face_landmark_5[index][1]), 3, primary_color, -1)
	if 'face-landmark-5/68' in frame_processors_globals.face_debugger_items and numpy.any(target_face.landmarks.get('5/68')):
		face_landmark_5_68 = target_face.landmarks.get('5/68').astype(numpy.int32)
		for index in range(face_landmark_5_68.shape[0]):
			cv2.circle(temp_vision_frame, (face_landmark_5_68[index][0], face_landmark_5_68[index][1]), 3, tertiary_color if has_face_landmark_5_fallback else secondary_color, -1)
	if 'face-landmark-68' in frame_processors_globals.face_debugger_items and numpy.any(target_face.landmarks.get('68')):
		face_landmark_68 = target_face.landmarks.get('68').astype(numpy.int32)
		for index in range(face_landmark_68.shape[0]):
			cv2.circle(temp_vision_frame, (face_landmark_68[index][0], face_landmark_68[index][1]), 3, tertiary_color if has_face_landmark_68_fallback else secondary_color, -1)
	if 'face-landmark-68/5' in frame_processors_globals.face_debugger_items and numpy.any(target_face.landmarks.get('68')):
		face_landmark_68 = target_face.landmarks.get('68/5').astype(numpy.int32)
		for index in range(face_landmark_68.shape[0]):
			cv2.circle(temp_vision_frame, (face_landmark_68[index][0], face_landmark_68[index][1]), 3, primary_color, -1)
	if bounding_box[3] - bounding_box[1] > 50 and bounding_box[2] - bounding_box[0] > 50:
		top = bounding_box[1]
		left = bounding_box[0] - 20
		if 'face-detector-score' in frame_processors_globals.face_debugger_items:
			face_score_text = str(round(target_face.scores.get('detector'), 2))
			top = top + 20
			cv2.putText(temp_vision_frame, face_score_text, (left, top), cv2.FONT_HERSHEY_SIMPLEX, 0.5, primary_color, 2)
		if 'face-landmarker-score' in frame_processors_globals.face_debugger_items:
			face_score_text = str(round(target_face.scores.get('landmarker'), 2))
			top = top + 20
			cv2.putText(temp_vision_frame, face_score_text, (left, top), cv2.FONT_HERSHEY_SIMPLEX, 0.5, tertiary_color if has_face_landmark_5_fallback else secondary_color, 2)
		if 'age' in frame_processors_globals.face_debugger_items:
			face_age_text = categorize_age(target_face.age)
			top = top + 20
			cv2.putText(temp_vision_frame, face_age_text, (left, top), cv2.FONT_HERSHEY_SIMPLEX, 0.5, primary_color, 2)
		if 'gender' in frame_processors_globals.face_debugger_items:
			face_gender_text = categorize_gender(target_face.gender)
			top = top + 20
			cv2.putText(temp_vision_frame, face_gender_text, (left, top), cv2.FONT_HERSHEY_SIMPLEX, 0.5, primary_color, 2)
	return temp_vision_frame


def get_reference_frame(source_face : Face, target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	pass


def process_frame(inputs : FaceDebuggerInputs) -> VisionFrame:
	reference_faces = inputs.get('reference_faces')
	target_vision_frame = inputs.get('target_vision_frame')

	if facefusion.globals.face_selector_mode == 'many':
		many_faces = get_many_faces(target_vision_frame)
		if many_faces:
			for target_face in many_faces:
				target_vision_frame = debug_face(target_face, target_vision_frame)
	if facefusion.globals.face_selector_mode == 'one':
		target_face = get_one_face(target_vision_frame)
		if target_face:
			target_vision_frame = debug_face(target_face, target_vision_frame)
	if facefusion.globals.face_selector_mode == 'reference':
		similar_faces = find_similar_faces(reference_faces, target_vision_frame, facefusion.globals.reference_face_distance)
		if similar_faces:
			for similar_face in similar_faces:
				target_vision_frame = debug_face(similar_face, target_vision_frame)
	return target_vision_frame


def process_frames(source_paths : List[str], queue_payloads : List[QueuePayload], update_progress : UpdateProgress) -> None:
	reference_faces = get_reference_faces() if 'reference' in facefusion.globals.face_selector_mode else None

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
	reference_faces = get_reference_faces() if 'reference' in facefusion.globals.face_selector_mode else None
	target_vision_frame = read_static_image(target_path)
	output_vision_frame = process_frame(
	{
		'reference_faces': reference_faces,
		'target_vision_frame': target_vision_frame
	})
	write_image(output_path, output_vision_frame)


def process_video(source_paths : List[str], temp_frame_paths : List[str]) -> None:
	frame_processors.multi_process_frames(source_paths, temp_frame_paths, process_frames)
