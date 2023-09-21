from typing import Any, List, Callable
import threading
from gfpgan.utils import GFPGANer

import facefusion.globals
from facefusion import wording, utilities
from facefusion.core import update_status
from facefusion.face_analyser import get_many_faces, clear_face_analyser
from facefusion.typing import Frame, Face, ProcessMode
from facefusion.utilities import conditional_download, resolve_relative_path, is_image, is_video, is_file, is_download_done
from facefusion.vision import read_image, read_static_image, write_image

FRAME_PROCESSOR = None
THREAD_SEMAPHORE : threading.Semaphore = threading.Semaphore()
THREAD_LOCK : threading.Lock = threading.Lock()
NAME = 'FACEFUSION.FRAME_PROCESSOR.FACE_ENHANCER'
MODEL_URL = 'https://github.com/facefusion/facefusion-assets/releases/download/models/GFPGANv1.4.pth'
MODEL_PATH = resolve_relative_path('../.assets/models/GFPGANv1.4.pth')


def get_frame_processor() -> Any:
	global FRAME_PROCESSOR

	with THREAD_LOCK:
		if FRAME_PROCESSOR is None:
			FRAME_PROCESSOR = GFPGANer(
				model_path = MODEL_PATH,
				upscale = 1,
				device = utilities.get_device(facefusion.globals.execution_providers)
			)
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
	if not is_download_done(MODEL_URL, MODEL_PATH):
		update_status(wording.get('model_download_not_done') + wording.get('exclamation_mark'), NAME)
		return False
	elif not is_file(MODEL_PATH):
		update_status(wording.get('model_file_not_present') + wording.get('exclamation_mark'), NAME)
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


def enhance_face(target_face : Face, temp_frame : Frame) -> Frame:
	start_x, start_y, end_x, end_y = map(int, target_face['bbox'])
	padding_x = int((end_x - start_x) * 0.5)
	padding_y = int((end_y - start_y) * 0.5)
	start_x = max(0, start_x - padding_x)
	start_y = max(0, start_y - padding_y)
	end_x = max(0, end_x + padding_x)
	end_y = max(0, end_y + padding_y)
	crop_frame = temp_frame[start_y:end_y, start_x:end_x]
	if crop_frame.size:
		with THREAD_SEMAPHORE:
			_, _, crop_frame = get_frame_processor().enhance(
				crop_frame,
				paste_back = True
			)
		temp_frame[start_y:end_y, start_x:end_x] = crop_frame
	return temp_frame


def process_frame(source_face : Face, reference_face : Face, temp_frame : Frame) -> Frame:
	many_faces = get_many_faces(temp_frame)
	if many_faces:
		for target_face in many_faces:
			temp_frame = enhance_face(target_face, temp_frame)
	return temp_frame


def process_frames(source_path : str, temp_frame_paths : List[str], update_progress: Callable[[], None]) -> None:
	for temp_frame_path in temp_frame_paths:
		temp_frame = read_image(temp_frame_path)
		result_frame = process_frame(None, None, temp_frame)
		write_image(temp_frame_path, result_frame)
		update_progress()


def process_image(source_path : str, target_path : str, output_path : str) -> None:
	target_frame = read_static_image(target_path)
	result_frame = process_frame(None, None, target_frame)
	write_image(output_path, result_frame)


def process_video(source_path : str, temp_frame_paths : List[str]) -> None:
	facefusion.processors.frame.core.multi_process_frames(None, temp_frame_paths, process_frames)
