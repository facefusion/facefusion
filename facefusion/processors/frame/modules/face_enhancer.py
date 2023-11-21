from typing import Any, List, Dict, Literal, Optional
from argparse import ArgumentParser
import cv2
import threading
import numpy
import onnxruntime

import facefusion.globals
import facefusion.processors.frame.core as frame_processors
from facefusion import wording
from facefusion.face_analyser import get_many_faces, clear_face_analyser
from facefusion.face_helper import warp_face, paste_back
from facefusion.content_analyser import clear_content_analyser
from facefusion.typing import Face, Frame, Update_Process, ProcessMode, ModelValue, OptionsWithModel
from facefusion.utilities import conditional_download, resolve_relative_path, is_image, is_video, is_file, is_download_done, create_metavar, update_status
from facefusion.vision import read_image, read_static_image, write_image
from facefusion.processors.frame import globals as frame_processors_globals
from facefusion.processors.frame import choices as frame_processors_choices

FRAME_PROCESSOR = None
THREAD_SEMAPHORE : threading.Semaphore = threading.Semaphore()
THREAD_LOCK : threading.Lock = threading.Lock()
NAME = 'FACEFUSION.FRAME_PROCESSOR.FACE_ENHANCER'
MODELS : Dict[str, ModelValue] =\
{
	'codeformer':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/codeformer.onnx',
		'path': resolve_relative_path('../.assets/models/codeformer.onnx'),
		'template': 'ffhq',
		'size': (512, 512)
	},
	'gfpgan_1.2':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/gfpgan_1.2.onnx',
		'path': resolve_relative_path('../.assets/models/gfpgan_1.2.onnx'),
		'template': 'ffhq',
		'size': (512, 512)
	},
	'gfpgan_1.3':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/gfpgan_1.3.onnx',
		'path': resolve_relative_path('../.assets/models/gfpgan_1.3.onnx'),
		'template': 'ffhq',
		'size': (512, 512)
	},
	'gfpgan_1.4':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/gfpgan_1.4.onnx',
		'path': resolve_relative_path('../.assets/models/gfpgan_1.4.onnx'),
		'template': 'ffhq',
		'size': (512, 512)
	},
	'gpen_bfr_256':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/gpen_bfr_256.onnx',
		'path': resolve_relative_path('../.assets/models/gpen_bfr_256.onnx'),
		'template': 'arcface_v2',
		'size': (128, 256)
	},
	'gpen_bfr_512':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/gpen_bfr_512.onnx',
		'path': resolve_relative_path('../.assets/models/gpen_bfr_512.onnx'),
		'template': 'ffhq',
		'size': (512, 512)
	},
	'restoreformer':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/restoreformer.onnx',
		'path': resolve_relative_path('../.assets/models/restoreformer.onnx'),
		'template': 'ffhq',
		'size': (512, 512)
	}
}
OPTIONS : Optional[OptionsWithModel] = None


def get_frame_processor() -> Any:
	global FRAME_PROCESSOR

	with THREAD_LOCK:
		if FRAME_PROCESSOR is None:
			model_path = get_options('model').get('path')
			FRAME_PROCESSOR = onnxruntime.InferenceSession(model_path, providers = facefusion.globals.execution_providers)
	return FRAME_PROCESSOR


def clear_frame_processor() -> None:
	global FRAME_PROCESSOR

	FRAME_PROCESSOR = None


def get_options(key : Literal['model']) -> Any:
	global OPTIONS

	if OPTIONS is None:
		OPTIONS =\
		{
			'model': MODELS[frame_processors_globals.face_enhancer_model]
		}
	return OPTIONS.get(key)


def set_options(key : Literal['model'], value : Any) -> None:
	global OPTIONS

	OPTIONS[key] = value


def register_args(program : ArgumentParser) -> None:
	program.add_argument('--face-enhancer-model', help = wording.get('frame_processor_model_help'), dest = 'face_enhancer_model', default = 'gfpgan_1.4', choices = frame_processors_choices.face_enhancer_models)
	program.add_argument('--face-enhancer-blend', help = wording.get('frame_processor_blend_help'), dest = 'face_enhancer_blend', type = int, default = 80, choices = frame_processors_choices.face_enhancer_blend_range, metavar = create_metavar(frame_processors_choices.face_enhancer_blend_range))


def apply_args(program : ArgumentParser) -> None:
	args = program.parse_args()
	frame_processors_globals.face_enhancer_model = args.face_enhancer_model
	frame_processors_globals.face_enhancer_blend = args.face_enhancer_blend


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
		update_status(wording.get('model_download_not_done') + wording.get('exclamation_mark'), NAME)
		return False
	elif not is_file(model_path):
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
	clear_content_analyser()
	read_static_image.cache_clear()


def enhance_face(target_face: Face, temp_frame: Frame) -> Frame:
	frame_processor = get_frame_processor()
	model_template = get_options('model').get('template')
	model_size = get_options('model').get('size')
	crop_frame, affine_matrix = warp_face(temp_frame, target_face.kps, model_template, model_size)
	crop_frame = prepare_crop_frame(crop_frame)
	frame_processor_inputs = {}
	for frame_processor_input in frame_processor.get_inputs():
		if frame_processor_input.name == 'input':
			frame_processor_inputs[frame_processor_input.name] = crop_frame
		if frame_processor_input.name == 'weight':
			frame_processor_inputs[frame_processor_input.name] = numpy.array([ 1 ], dtype = numpy.double)
	with THREAD_SEMAPHORE:
		crop_frame = frame_processor.run(None, frame_processor_inputs)[0][0]
	crop_frame = normalize_crop_frame(crop_frame)
	paste_frame = paste_back(temp_frame, crop_frame, affine_matrix, facefusion.globals.face_mask_blur, (0, 0, 0, 0))
	temp_frame = blend_frame(temp_frame, paste_frame)
	return temp_frame


def prepare_crop_frame(crop_frame : Frame) -> Frame:
	crop_frame = crop_frame[:, :, ::-1] / 255.0
	crop_frame = (crop_frame - 0.5) / 0.5
	crop_frame = numpy.expand_dims(crop_frame.transpose(2, 0, 1), axis = 0).astype(numpy.float32)
	return crop_frame


def normalize_crop_frame(crop_frame : Frame) -> Frame:
	crop_frame = numpy.clip(crop_frame, -1, 1)
	crop_frame = (crop_frame + 1) / 2
	crop_frame = crop_frame.transpose(1, 2, 0)
	crop_frame = (crop_frame * 255.0).round()
	crop_frame = crop_frame.astype(numpy.uint8)[:, :, ::-1]
	return crop_frame


def blend_frame(temp_frame : Frame, paste_frame : Frame) -> Frame:
	face_enhancer_blend = 1 - (frame_processors_globals.face_enhancer_blend / 100)
	temp_frame = cv2.addWeighted(temp_frame, face_enhancer_blend, paste_frame, 1 - face_enhancer_blend, 0)
	return temp_frame


def process_frame(source_face : Face, reference_face : Face, temp_frame : Frame) -> Frame:
	many_faces = get_many_faces(temp_frame)
	if many_faces:
		for target_face in many_faces:
			temp_frame = enhance_face(target_face, temp_frame)
	return temp_frame


def process_frames(source_path : str, temp_frame_paths : List[str], update_progress : Update_Process) -> None:
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
	frame_processors.multi_process_frames(None, temp_frame_paths, process_frames)
