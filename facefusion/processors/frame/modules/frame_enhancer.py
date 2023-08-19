from typing import Any, List, Callable
import cv2
import threading
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

import facefusion.processors.frame.core as frame_processors
from facefusion.typing import Frame, Face
from facefusion.utilities import conditional_download, resolve_relative_path

FRAME_PROCESSOR = None
THREAD_SEMAPHORE = threading.Semaphore()
THREAD_LOCK = threading.Lock()
NAME = 'FACEFUSION.FRAME_PROCESSOR.FRAME_ENHANCER'


def get_frame_processor() -> Any:
	global FRAME_PROCESSOR

	with THREAD_LOCK:
		if FRAME_PROCESSOR is None:
			model_path = resolve_relative_path('../.assets/models/RealESRGAN_x4plus.pth')
			FRAME_PROCESSOR = RealESRGANer(
				model_path = model_path,
				model = RRDBNet(
					num_in_ch = 3,
					num_out_ch = 3,
					num_feat = 64,
					num_block = 23,
					num_grow_ch = 32,
					scale = 4
				),
				device = frame_processors.get_device(),
				tile = 512,
				tile_pad = 32,
				pre_pad = 0,
				scale = 4
			)
	return FRAME_PROCESSOR


def clear_frame_processor() -> None:
	global FRAME_PROCESSOR

	FRAME_PROCESSOR = None


def pre_check() -> bool:
	download_directory_path = resolve_relative_path('../.assets/models')
	conditional_download(download_directory_path, ['https://huggingface.co/facefusion/models/resolve/main/RealESRGAN_x4plus.pth'])
	return True


def pre_process() -> bool:
	return True


def post_process() -> None:
	clear_frame_processor()


def enhance_frame(temp_frame : Frame) -> Frame:
	with THREAD_SEMAPHORE:
		temp_frame, _ = get_frame_processor().enhance(temp_frame, outscale = 1)
	return temp_frame


def process_frame(source_face : Face, reference_face : Face, temp_frame : Frame) -> Frame:
	return enhance_frame(temp_frame)


def process_frames(source_path : str, temp_frame_paths : List[str], update: Callable[[], None]) -> None:
	for temp_frame_path in temp_frame_paths:
		temp_frame = cv2.imread(temp_frame_path)
		result_frame = process_frame(None, None, temp_frame)
		cv2.imwrite(temp_frame_path, result_frame)
		if update:
			update()


def process_image(source_path : str, target_path : str, output_path : str) -> None:
	target_frame = cv2.imread(target_path)
	result = process_frame(None, None, target_frame)
	cv2.imwrite(output_path, result)


def process_video(source_path : str, temp_frame_paths : List[str]) -> None:
	frame_processors.process_video(None, temp_frame_paths, process_frames)
