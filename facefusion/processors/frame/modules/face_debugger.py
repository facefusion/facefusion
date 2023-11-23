from typing import Any, List, Literal
from argparse import ArgumentParser
import cv2
import numpy

import facefusion.globals
import facefusion.processors.frame.core as frame_processors
from facefusion import wording
from facefusion.face_analyser import get_one_face, get_many_faces, find_similar_faces, clear_face_analyser
from facefusion.face_reference import get_face_reference
from facefusion.content_analyser import clear_content_analyser
from facefusion.typing import Face, Frame, Update_Process, ProcessMode
from facefusion.vision import read_image, read_static_image, write_image
from facefusion.face_helper import warp_face, create_static_mask_frame
from facefusion.processors.frame import globals as frame_processors_globals, choices as frame_processors_choices

NAME = 'FACEFUSION.FRAME_PROCESSOR.FACE_DEBUGGER'


def get_frame_processor() -> None:
	pass


def clear_frame_processor() -> None:
	pass


def get_options(key : Literal['model']) -> None:
	pass


def set_options(key : Literal['model'], value : Any) -> None:
	pass


def register_args(program : ArgumentParser) -> None:
	program.add_argument('--face-debugger-items', help = wording.get('face_debugger_items_help'), dest = 'face_debugger_items', default = [ 'kps', 'face-mask' ], choices = frame_processors_choices.face_debugger_items, nargs = '+')


def apply_args(program : ArgumentParser) -> None:
	args = program.parse_args()
	frame_processors_globals.face_debugger_items = args.face_debugger_items


def pre_check() -> bool:
	return True


def pre_process(mode : ProcessMode) -> bool:
	return True


def post_process() -> None:
	clear_frame_processor()
	clear_face_analyser()
	clear_content_analyser()


def debug_face(source_face : Face, target_face : Face, temp_frame : Frame) -> Frame:
	primary_color = (0, 0, 255)
	secondary_color = (0, 255, 0)
	bounding_box = target_face.bbox.astype(numpy.int32)
	if 'bbox' in frame_processors_globals.face_debugger_items:
		cv2.rectangle(temp_frame, (bounding_box[0], bounding_box[1]), (bounding_box[2], bounding_box[3]), secondary_color, 2)
	if 'face-mask' in frame_processors_globals.face_debugger_items:
		crop_frame, affine_matrix = warp_face(temp_frame, target_face.kps, 'arcface_v2', (128, 128))
		inverse_matrix = cv2.invertAffineTransform(affine_matrix)
		temp_frame_size = temp_frame.shape[:2][::-1]
		mask_frame = create_static_mask_frame(crop_frame.shape[:2], 0, facefusion.globals.face_mask_padding)
		mask_frame[mask_frame > 0] = 255
		inverse_mask_frame = cv2.warpAffine(mask_frame.astype(numpy.uint8), inverse_matrix, temp_frame_size)
		inverse_mask_contours = cv2.findContours(inverse_mask_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
		cv2.drawContours(temp_frame, inverse_mask_contours, 0, primary_color, 2)
	if bounding_box[3] - bounding_box[1] > 60 and bounding_box[2] - bounding_box[0] > 60:
		if 'kps' in frame_processors_globals.face_debugger_items:
			kps = target_face.kps.astype(numpy.int32)
			for index in range(kps.shape[0]):
				cv2.circle(temp_frame, (kps[index][0], kps[index][1]), 3, primary_color, -1)
		if 'score' in frame_processors_globals.face_debugger_items:
			score_text = str(round(target_face.score, 2))
			score_position = (bounding_box[0] + 10, bounding_box[1] + 20)
			cv2.putText(temp_frame, score_text, score_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, secondary_color, 2)
	return temp_frame


def process_frame(source_face : Face, reference_face : Face, temp_frame : Frame) -> Frame:
	if 'reference' in facefusion.globals.face_selector_mode:
		similar_faces = find_similar_faces(temp_frame, reference_face, facefusion.globals.reference_face_distance)
		if similar_faces:
			for similar_face in similar_faces:
				temp_frame = debug_face(source_face, similar_face, temp_frame)
	if 'one' in facefusion.globals.face_selector_mode:
		target_face = get_one_face(temp_frame)
		if target_face:
			temp_frame = debug_face(source_face, target_face, temp_frame)
	if 'many' in facefusion.globals.face_selector_mode:
		many_faces = get_many_faces(temp_frame)
		if many_faces:
			for target_face in many_faces:
				temp_frame = debug_face(source_face, target_face, temp_frame)
	return temp_frame


def process_frames(source_path : str, temp_frame_paths : List[str], update_progress : Update_Process) -> None:
	source_face = get_one_face(read_static_image(source_path))
	reference_face = get_face_reference() if 'reference' in facefusion.globals.face_selector_mode else None
	for temp_frame_path in temp_frame_paths:
		temp_frame = read_image(temp_frame_path)
		result_frame = process_frame(source_face, reference_face, temp_frame)
		write_image(temp_frame_path, result_frame)
		update_progress()


def process_image(source_path : str, target_path : str, output_path : str) -> None:
	source_face = get_one_face(read_static_image(source_path))
	target_frame = read_static_image(target_path)
	reference_face = get_one_face(target_frame, facefusion.globals.reference_face_position) if 'reference' in facefusion.globals.face_selector_mode else None
	result_frame = process_frame(source_face, reference_face, target_frame)
	write_image(output_path, result_frame)


def process_video(source_path : str, temp_frame_paths : List[str]) -> None:
	frame_processors.multi_process_frames(source_path, temp_frame_paths, process_frames)
