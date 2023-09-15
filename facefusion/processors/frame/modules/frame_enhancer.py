from typing import Any, List, Callable
import threading
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

import facefusion
import facefusion.processors.frame.core as frame_processors
from facefusion import wording, utilities
from facefusion.core import update_status
from facefusion.typing import Frame, Face, ProcessMode
from facefusion.utilities import conditional_download, resolve_relative_path
from facefusion.vision import read_image, read_static_image, write_image

FRAME_PROCESSOR = None
THREAD_SEMAPHORE : threading.Semaphore = threading.Semaphore()
THREAD_LOCK : threading.Lock = threading.Lock()
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
				device = utilities.get_device(facefusion.globals.execution_providers),
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
	conditional_download(download_directory_path, [ 'https://github.com/facefusion/facefusion-assets/releases/download/models/RealESRGAN_x4plus.pth' ])
	return True


def pre_process(mode : ProcessMode) -> bool:
	if mode == 'output' and not facefusion.globals.output_path:
		update_status(wording.get('select_file_or_directory_output') + wording.get('exclamation_mark'), NAME)
		return False
	return True


def post_process() -> None:
	clear_frame_processor()
	read_static_image.cache_clear()


def enhance_frame(temp_frame : Frame) -> Frame:
	with THREAD_SEMAPHORE:
		temp_frame, _ = get_frame_processor().enhance(temp_frame, outscale = 1)
	return temp_frame


def process_frame(source_face : Face, reference_face : Face, temp_frame : Frame) -> Frame:
	return enhance_frame(temp_frame)


def process_frames(source_path : str, temp_frame_paths : List[str], update_progress: Callable[[], None]) -> None:
	for temp_frame_path in temp_frame_paths:
		temp_frame = read_image(temp_frame_path)
		result_frame = process_frame(None, None, temp_frame)
		write_image(temp_frame_path, result_frame)
		update_progress()


def process_image(source_path : str, target_path : str, output_path : str) -> None:
	target_frame = read_static_image(target_path)
	result = process_frame(None, None, target_frame)
	write_image(output_path, result)


def process_video(source_path : str, temp_frame_paths : List[str]) -> None:
	frame_processors.multi_process_frames(None, temp_frame_paths, process_frames)
