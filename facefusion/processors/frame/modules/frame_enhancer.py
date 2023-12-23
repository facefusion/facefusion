from typing import Any, List, Literal, Optional
from argparse import ArgumentParser
import threading
import cv2
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

import facefusion.globals
import facefusion.processors.frame.core as frame_processors
from facefusion import logger, wording
from facefusion.face_analyser import clear_face_analyser
from facefusion.content_analyser import clear_content_analyser
from facefusion.typing import Face, FaceSet, Frame, Update_Process, ProcessMode, ModelSet, OptionsWithModel
from facefusion.common_helper import create_metavar
from facefusion.execution_helper import map_device
from facefusion.filesystem import is_file, resolve_relative_path
from facefusion.download import conditional_download, is_download_done
from facefusion.vision import read_image, read_static_image, write_image
from facefusion.processors.frame import globals as frame_processors_globals
from facefusion.processors.frame import choices as frame_processors_choices

FRAME_PROCESSOR = None
THREAD_SEMAPHORE : threading.Semaphore = threading.Semaphore()
THREAD_LOCK : threading.Lock = threading.Lock()
NAME = __name__.upper()
MODELS : ModelSet =\
{
	'real_esrgan_x2plus':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/real_esrgan_x2plus.pth',
		'path': resolve_relative_path('../.assets/models/real_esrgan_x2plus.pth'),
		'scale': 2
	},
	'real_esrgan_x4plus':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/real_esrgan_x4plus.pth',
		'path': resolve_relative_path('../.assets/models/real_esrgan_x4plus.pth'),
		'scale': 4
	},
	'real_esrnet_x4plus':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/real_esrnet_x4plus.pth',
		'path': resolve_relative_path('../.assets/models/real_esrnet_x4plus.pth'),
		'scale': 4
	}
}
OPTIONS : Optional[OptionsWithModel] = None


def get_frame_processor() -> Any:
	global FRAME_PROCESSOR

	with THREAD_LOCK:
		if FRAME_PROCESSOR is None:
			model_path = get_options('model').get('path')
			model_scale = get_options('model').get('scale')
			FRAME_PROCESSOR = RealESRGANer(
				model_path = model_path,
				model = RRDBNet(
					num_in_ch = 3,
					num_out_ch = 3,
					scale = model_scale
				),
				device = map_device(facefusion.globals.execution_providers),
				scale = model_scale
			)
	return FRAME_PROCESSOR


def clear_frame_processor() -> None:
	global FRAME_PROCESSOR

	FRAME_PROCESSOR = None


def get_options(key : Literal['model']) -> Any:
	global OPTIONS

	if OPTIONS is None:
		OPTIONS =\
		{
			'model': MODELS[frame_processors_globals.frame_enhancer_model]
		}
	return OPTIONS.get(key)


def set_options(key : Literal['model'], value : Any) -> None:
	global OPTIONS

	OPTIONS[key] = value


def register_args(program : ArgumentParser) -> None:
	program.add_argument('--frame-enhancer-model', help = wording.get('frame_processor_model_help'), default = 'real_esrgan_x2plus', choices = frame_processors_choices.frame_enhancer_models)
	program.add_argument('--frame-enhancer-blend', help = wording.get('frame_processor_blend_help'), type = int, default = 80, choices = frame_processors_choices.frame_enhancer_blend_range, metavar = create_metavar(frame_processors_choices.frame_enhancer_blend_range))


def apply_args(program : ArgumentParser) -> None:
	args = program.parse_args()
	frame_processors_globals.frame_enhancer_model = args.frame_enhancer_model
	frame_processors_globals.frame_enhancer_blend = args.frame_enhancer_blend


def pre_check() -> bool:
	if not facefusion.globals.skip_download:
		download_directory_path = resolve_relative_path('../.assets/models')
		model_url = get_options('model').get('url')
		conditional_download(download_directory_path, [ model_url ])
	return True


def pre_process(mode : ProcessMode) -> bool:
	model_url = get_options('model').get('url')
	model_path = get_options('model').get('path')
	if not facefusion.globals.skip_download and not is_download_done(model_url, model_path):
		logger.error(wording.get('model_download_not_done') + wording.get('exclamation_mark'), NAME)
		return False
	elif not is_file(model_path):
		logger.error(wording.get('model_file_not_present') + wording.get('exclamation_mark'), NAME)
		return False
	if mode == 'output' and not facefusion.globals.output_path:
		logger.error(wording.get('select_file_or_directory_output') + wording.get('exclamation_mark'), NAME)
		return False
	return True


def post_process() -> None:
	clear_frame_processor()
	clear_face_analyser()
	clear_content_analyser()
	read_static_image.cache_clear()


def enhance_frame(temp_frame : Frame) -> Frame:
	with THREAD_SEMAPHORE:
		paste_frame, _ = get_frame_processor().enhance(temp_frame)
		temp_frame = blend_frame(temp_frame, paste_frame)
	return temp_frame


def blend_frame(temp_frame : Frame, paste_frame : Frame) -> Frame:
	frame_enhancer_blend = 1 - (frame_processors_globals.frame_enhancer_blend / 100)
	paste_frame_height, paste_frame_width = paste_frame.shape[0:2]
	temp_frame = cv2.resize(temp_frame, (paste_frame_width, paste_frame_height))
	temp_frame = cv2.addWeighted(temp_frame, frame_enhancer_blend, paste_frame, 1 - frame_enhancer_blend, 0)
	return temp_frame


def get_reference_frame(source_face : Face, target_face : Face, temp_frame : Frame) -> Frame:
	pass


def process_frame(source_face : Face, reference_faces : FaceSet, temp_frame : Frame) -> Frame:
	return enhance_frame(temp_frame)


def process_frames(source_paths : List[str], temp_frame_paths : List[str], update_progress : Update_Process) -> None:
	for temp_frame_path in temp_frame_paths:
		temp_frame = read_image(temp_frame_path)
		result_frame = process_frame(None, None, temp_frame)
		write_image(temp_frame_path, result_frame)
		update_progress()


def process_image(source_paths : List[str], target_path : str, output_path : str) -> None:
	target_frame = read_static_image(target_path)
	result = process_frame(None, None, target_frame)
	write_image(output_path, result)


def process_video(source_paths : List[str], temp_frame_paths : List[str]) -> None:
	frame_processors.multi_process_frames(None, temp_frame_paths, process_frames)
