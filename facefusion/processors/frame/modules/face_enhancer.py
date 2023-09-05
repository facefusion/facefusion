from typing import Any, List, Callable
import cv2
import threading
from gfpgan.utils import GFPGANer

import facefusion.globals
from facefusion import wording, utilities
from facefusion.core import update_status
from facefusion.face_analyser import get_many_faces
from facefusion.typing import Frame, Face, ProcessMode
from facefusion.utilities import conditional_download, resolve_relative_path, is_image, is_video

FRAME_PROCESSOR = None
THREAD_SEMAPHORE = threading.Semaphore()
THREAD_LOCK = threading.Lock()
NAME = 'FACEFUSION.FRAME_PROCESSOR.FACE_ENHANCER'


def get_frame_processor() -> Any:
	global FRAME_PROCESSOR

	with THREAD_LOCK:
		if FRAME_PROCESSOR is None:
			model_path = resolve_relative_path('../.assets/models/GFPGANv1.4.pth')
			FRAME_PROCESSOR = GFPGANer(
				model_path = model_path,
				upscale = 1,
				device = utilities.get_device(facefusion.globals.execution_providers)
			)
	return FRAME_PROCESSOR


def clear_frame_processor() -> None:
	global FRAME_PROCESSOR

	FRAME_PROCESSOR = None


def pre_check() -> bool:
	download_directory_path = resolve_relative_path('../.assets/models')
	conditional_download(download_directory_path, [ 'https://github.com/facefusion/facefusion-assets/releases/download/models/GFPGANv1.4.pth' ])
	return True


def pre_process(mode : ProcessMode) -> bool:
	if mode in [ 'output', 'preview' ] and not is_image(facefusion.globals.target_path) and not is_video(facefusion.globals.target_path):
		update_status(wording.get('select_image_or_video_target') + wording.get('exclamation_mark'), NAME)
		return False
	if mode == 'output' and not facefusion.globals.output_path:
		update_status(wording.get('select_file_or_directory_output') + wording.get('exclamation_mark'), NAME)
		return False
	return True


def post_process() -> None:
	clear_frame_processor()


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


def process_frames(source_path : str, temp_frame_paths : List[str], update: Callable[[], None]) -> None:
	for temp_frame_path in temp_frame_paths:
		temp_frame = cv2.imread(temp_frame_path)
		result_frame = process_frame(None, None, temp_frame)
		cv2.imwrite(temp_frame_path, result_frame)
		if update:
			update()


def process_image(source_path : str, target_path : str, output_path : str) -> None:
	target_frame = cv2.imread(target_path)
	result_frame = process_frame(None, None, target_frame)
	cv2.imwrite(output_path, result_frame)


def process_video(source_path : str, temp_frame_paths : List[str]) -> None:
	facefusion.processors.frame.core.process_video(None, temp_frame_paths, process_frames)
