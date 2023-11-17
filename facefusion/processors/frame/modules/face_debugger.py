from typing import Any, List, Literal
from argparse import ArgumentParser
import cv2
import numpy

import facefusion.globals
import facefusion.processors.frame.core as frame_processors
from facefusion.face_analyser import get_one_face, get_many_faces, find_similar_faces, clear_face_analyser
from facefusion.face_reference import get_face_reference
from facefusion.content_analyser import clear_content_analyser
from facefusion.typing import Face, Frame, Update_Process, ProcessMode
from facefusion.vision import read_image, read_static_image, write_image

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
	pass


def apply_args(program : ArgumentParser) -> None:
	pass


def pre_check() -> bool:
	return True


def pre_process(mode : ProcessMode) -> bool:
	return True


def post_process() -> None:
	clear_frame_processor()
	clear_face_analyser()
	clear_content_analyser()


def debug_face(source_face: Face, target_face: Face, temp_frame: Frame) -> Frame:
	primary_color = (0, 0, 255)
	secondary_color = (0, 255, 0)
	face_mask_padding = facefusion.globals.face_mask_padding
	bounding_box = target_face.bbox.astype(numpy.int32)
	padding_box =\
	[
		int(bounding_box[1] + (bounding_box[3] - bounding_box[1]) * face_mask_padding[0] / 100),
		int(bounding_box[2] - (bounding_box[2] - bounding_box[0]) * face_mask_padding[1] / 100),
		int(bounding_box[3] - (bounding_box[3] - bounding_box[1]) * face_mask_padding[2] / 100),
		int(bounding_box[0] + (bounding_box[2] - bounding_box[0]) * face_mask_padding[3] / 100)
	]
	cv2.rectangle(temp_frame, (bounding_box[0], bounding_box[1]), (bounding_box[2], bounding_box[3]), primary_color, 2)
	cv2.rectangle(temp_frame, (padding_box[3], padding_box[0]), (padding_box[1], padding_box[2]), secondary_color, 2)
	if bounding_box[3] - bounding_box[1] > 60 and bounding_box[2] - bounding_box[0] > 60:
		kps = target_face.kps.astype(numpy.int32)
		for index in range(kps.shape[0]):
			cv2.circle(temp_frame, (kps[index][0], kps[index][1]), 3, primary_color, -1)
	return temp_frame


def process_frame(source_face : Face, reference_face : Face, temp_frame : Frame) -> Frame:
	if 'reference' in facefusion.globals.face_selector_mode:
		similar_faces = find_similar_faces(temp_frame, reference_face, facefusion.globals.reference_face_distance)
		if similar_faces:
			for similar_face in similar_faces:
				temp_frame = debug_face(source_face, similar_face, temp_frame)
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
