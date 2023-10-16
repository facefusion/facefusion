from typing import Any, List, Dict, Literal, Optional
from argparse import ArgumentParser
import threading
import numpy
import onnx
import onnxruntime
from onnx import numpy_helper

import facefusion.globals
import facefusion.processors.frame.core as frame_processors
from facefusion import wording
from facefusion.face_analyser import get_one_face, get_many_faces, find_similar_faces, clear_face_analyser
from facefusion.face_helper import warp_face, paste_back
from facefusion.face_reference import get_face_reference, set_face_reference
from facefusion.predictor import clear_predictor
from facefusion.typing import Face, Frame, Update_Process, ProcessMode, ModelValue, OptionsWithModel
from facefusion.utilities import conditional_download, resolve_relative_path, is_image, is_video, is_file, is_download_done, update_status
from facefusion.vision import read_image, read_static_image, write_image
from facefusion.processors.frame import globals as frame_processors_globals
from facefusion.processors.frame import choices as frame_processors_choices

FRAME_PROCESSOR = None
MODEL_MATRIX = None
THREAD_LOCK : threading.Lock = threading.Lock()
NAME = 'FACEFUSION.FRAME_PROCESSOR.FACE_SWAPPER'
MODELS : Dict[str, ModelValue] =\
{
	'inswapper_128':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/inswapper_128.onnx',
		'path': resolve_relative_path('../.assets/models/inswapper_128.onnx'),
		'template': 'arcface',
		'size': (128, 128)
	},
	'inswapper_128_fp16':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/inswapper_128_fp16.onnx',
		'path': resolve_relative_path('../.assets/models/inswapper_128_fp16.onnx'),
		'template': 'arcface',
		'size': (128, 128)
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


def get_model_matrix() -> Any:
	global MODEL_MATRIX

	with THREAD_LOCK:
		if MODEL_MATRIX is None:
			model_path = get_options('model').get('path')
			model = onnx.load(model_path)
			MODEL_MATRIX = numpy_helper.to_array(model.graph.initializer[-1])
	return MODEL_MATRIX


def clear_model_matrix() -> None:
	global MODEL_MATRIX

	MODEL_MATRIX = None


def get_options(key : Literal[ 'model' ]) -> Any:
	global OPTIONS

	if OPTIONS is None:
		OPTIONS =\
		{
			'model': MODELS[frame_processors_globals.face_swapper_model]
		}
	return OPTIONS.get(key)


def set_options(key : Literal[ 'model' ], value : Any) -> None:
	global OPTIONS

	OPTIONS[key] = value


def register_args(program : ArgumentParser) -> None:
	program.add_argument('--face-swapper-model', help = wording.get('frame_processor_model_help'), dest = 'face_swapper_model', default = 'inswapper_128', choices = frame_processors_choices.face_swapper_models)


def apply_args(program : ArgumentParser) -> None:
	args = program.parse_args()
	frame_processors_globals.face_swapper_model = args.face_swapper_model


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
	clear_model_matrix()
	clear_face_analyser()
	clear_predictor()
	read_static_image.cache_clear()


def swap_face(source_face : Face, target_face : Face, temp_frame : Frame) -> Frame:
	frame_processor = get_frame_processor()
	model_template = get_options('model').get('template')
	model_size = get_options('model').get('size')
	source_face = prepare_source_face(source_face)
	crop_frame, affine_matrix = warp_face(temp_frame, target_face.kps, model_template, model_size)
	crop_frame = prepare_crop_frame(crop_frame)
	frame_processor_inputs = {}
	for frame_processor_input in frame_processor.get_inputs():
		if frame_processor_input.name == 'source':
			frame_processor_inputs[frame_processor_input.name] = source_face
		if frame_processor_input.name == 'target':
			frame_processor_inputs[frame_processor_input.name] = crop_frame
	crop_frame = frame_processor.run(None, frame_processor_inputs)[0][0]
	crop_frame = normalize_crop_frame(crop_frame)
	temp_frame = paste_back(temp_frame, crop_frame, affine_matrix)
	return temp_frame


def prepare_source_face(source_face : Face) -> Face:
	model_matrix = get_model_matrix()
	source_face = source_face.embedding.reshape((1, -1))
	source_face = numpy.dot(source_face, model_matrix) / numpy.linalg.norm(source_face)
	return source_face


def prepare_crop_frame(crop_frame : Frame) -> Frame:
	crop_frame = crop_frame / 255.0
	crop_frame = crop_frame[:, :, ::-1]
	crop_frame = numpy.expand_dims(crop_frame, axis = 0).transpose(0, 3, 1, 2).astype(numpy.float32)
	return crop_frame


def normalize_crop_frame(crop_frame : Frame) -> Frame:
	crop_frame = crop_frame.transpose(1, 2, 0)
	crop_frame = (crop_frame * 255.0).round()
	crop_frame = crop_frame.astype(numpy.uint8)[:, :, ::-1]
	return crop_frame


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


def process_frames(source_path : str, temp_frame_paths : List[str], update_progress : Update_Process) -> None:
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
