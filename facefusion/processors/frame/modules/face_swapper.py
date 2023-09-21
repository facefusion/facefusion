from typing import Any, List, Callable
import insightface
import threading

import facefusion.globals
import facefusion.processors.frame.core as frame_processors
from facefusion import wording
from facefusion.core import update_status
from facefusion.face_analyser import get_one_face, get_many_faces, find_similar_faces, clear_face_analyser
from facefusion.face_reference import get_face_reference, set_face_reference
from facefusion.typing import Face, Frame, ProcessMode
from facefusion.utilities import conditional_download, resolve_relative_path, is_image, is_video, is_file, is_download_done
from facefusion.vision import read_image, read_static_image, write_image

FRAME_PROCESSOR = None
THREAD_LOCK : threading.Lock = threading.Lock()
NAME = 'FACEFUSION.FRAME_PROCESSOR.FACE_SWAPPER'
MODEL_URL = 'https://github.com/facefusion/facefusion-assets/releases/download/models/inswapper_128.onnx'
MODEL_PATH = resolve_relative_path('../.assets/models/inswapper_128.onnx')


def get_frame_processor() -> Any:
	global FRAME_PROCESSOR

	with THREAD_LOCK:
		if FRAME_PROCESSOR is None:
			FRAME_PROCESSOR = insightface.model_zoo.get_model(MODEL_PATH, providers = facefusion.globals.execution_providers)
	return FRAME_PROCESSOR


def clear_frame_processor() -> None:
	global FRAME_PROCESSOR

	FRAME_PROCESSOR = None


def pre_check() -> bool:
	if not facefusion.globals.skip_download:
		download_directory_path = resolve_relative_path('../.assets/models')
		conditional_download(download_directory_path, [ MODEL_URL ])
	return True


def pre_process(mode : ProcessMode) -> bool:
	if not facefusion.globals.skip_download and not is_download_done(MODEL_URL, MODEL_PATH):
		update_status(wording.get('model_download_not_done') + wording.get('exclamation_mark'), NAME)
		return False
	elif not is_file(MODEL_PATH):
		update_status(wording.get('model_file_not_present') + wording.get('exclamation_mark'), NAME)
		return False
	if not is_image(facefusion.globals.source_path):
		update_status(wording.get('select_image_source') + wording.get('exclamation_mark'), NAME)
		return False
	elif not get_one_face(read_static_image(facefusion.globals.source_path)):
		update_status(wording.get('no_source_face_detected') + wording.get('exclamation_mark'), NAME)
		return False
	if mode in [ 'output', 'preview' ] and not is_image(facefusion.globals.target_path) and not is_video(facefusion.globals.target_path):
		update_status(wording.get('select_image_or_video_target') + wording.get('exclamation_mark'), NAME)
		return False
	if mode == 'output' and not facefusion.globals.output_path:
		update_status(wording.get('select_file_or_directory_output') + wording.get('exclamation_mark'), NAME)
		return False
	return True


def post_process() -> None:
	clear_frame_processor()
	clear_face_analyser()
	read_static_image.cache_clear()


def swap_face(source_face : Face, target_face : Face, temp_frame : Frame) -> Frame:
	return get_frame_processor().get(temp_frame, target_face, source_face, paste_back = True)


def process_frame(source_face : Face, reference_face : Face, temp_frame : Frame) -> Frame:
	if 'reference' in facefusion.globals.face_recognition:
		similar_faces = find_similar_faces(temp_frame, reference_face, facefusion.globals.reference_face_distance)
		if similar_faces:
			for similar_face in similar_faces:
				temp_frame = swap_face(source_face, similar_face, temp_frame)
	if 'many' in facefusion.globals.face_recognition:
		many_faces = get_many_faces(temp_frame)
		if many_faces:
			for target_face in many_faces:
				temp_frame = swap_face(source_face, target_face, temp_frame)
	return temp_frame


def process_frames(source_path : str, temp_frame_paths : List[str], update_progress: Callable[[], None]) -> None:
	source_face = get_one_face(read_static_image(source_path))
	reference_face = get_face_reference() if 'reference' in facefusion.globals.face_recognition else None
	for temp_frame_path in temp_frame_paths:
		temp_frame = read_image(temp_frame_path)
		result_frame = process_frame(source_face, reference_face, temp_frame)
		write_image(temp_frame_path, result_frame)
		update_progress()


def process_image(source_path : str, target_path : str, output_path : str) -> None:
	source_face = get_one_face(read_static_image(source_path))
	target_frame = read_static_image(target_path)
	reference_face = get_one_face(target_frame, facefusion.globals.reference_face_position) if 'reference' in facefusion.globals.face_recognition else None
	result_frame = process_frame(source_face, reference_face, target_frame)
	write_image(output_path, result_frame)


def process_video(source_path : str, temp_frame_paths : List[str]) -> None:
	conditional_set_face_reference(temp_frame_paths)
	frame_processors.multi_process_frames(source_path, temp_frame_paths, process_frames)


def conditional_set_face_reference(temp_frame_paths : List[str]) -> None:
	if 'reference' in facefusion.globals.face_recognition and not get_face_reference():
		reference_frame = read_static_image(temp_frame_paths[facefusion.globals.reference_frame_number])
		reference_face = get_one_face(reference_frame, facefusion.globals.reference_face_position)
		set_face_reference(reference_face)
