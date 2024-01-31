import os
from typing import Any, List, Literal, Optional
from argparse import ArgumentParser
import threading
import numpy
import onnxruntime

import facefusion.globals
import facefusion.processors.frame.core as frame_processors
from facefusion import config, logger, wording
from facefusion.execution_helper import apply_execution_provider_options
from facefusion.face_analyser import get_one_face, get_many_faces, find_similar_faces, clear_face_analyser
from facefusion.face_helper import paste_back, warp_face_by_kps, warp_face_by_bbox
from facefusion.face_store import get_reference_faces
from facefusion.content_analyser import clear_content_analyser
from facefusion.typing import Face, FaceSet, VisionFrame, Update_Process, ProcessMode, ModelSet, OptionsWithModel, AudioFrame
from facefusion.filesystem import is_file, resolve_relative_path
from facefusion.download import conditional_download, is_download_done
from facefusion.audio import read_static_audio, get_audio_frame
from facefusion.filesystem import is_video, filter_audio_paths
from facefusion.vision import read_image, write_image, detect_video_fps, read_static_image
from facefusion.processors.frame import globals as frame_processors_globals
from facefusion.processors.frame import choices as frame_processors_choices
from facefusion.face_masker import create_static_box_mask, create_occlusion_mask, clear_face_occluder, create_region_mask, clear_face_parser
from facefusion.common_helper import get_first_item

FRAME_PROCESSOR = None
MODEL_MATRIX = None
THREAD_LOCK : threading.Lock = threading.Lock()
NAME = __name__.upper()
MODELS : ModelSet =\
{
	'wav2lip':
	{
		'url': 'https://huggingface.co/bluefoxcreation/Wav2lip-Onnx/resolve/main/wav2lip_gan.onnx?download=true',
		'path': resolve_relative_path('../.assets/models/wav2lip_gan.onnx'),
	}
}
OPTIONS : Optional[OptionsWithModel] = None


def get_frame_processor() -> Any:
	global FRAME_PROCESSOR

	with THREAD_LOCK:
		if FRAME_PROCESSOR is None:
			model_path = get_options('model').get('path')
			FRAME_PROCESSOR = onnxruntime.InferenceSession(model_path, providers = apply_execution_provider_options(facefusion.globals.execution_providers))
	return FRAME_PROCESSOR


def clear_frame_processor() -> None:
	global FRAME_PROCESSOR

	FRAME_PROCESSOR = None


def get_options(key : Literal['model']) -> Any:
	global OPTIONS

	if OPTIONS is None:
		OPTIONS =\
		{
			'model': MODELS[frame_processors_globals.lip_syncer_model]
		}
	return OPTIONS.get(key)


def set_options(key : Literal['model'], value : Any) -> None:
	global OPTIONS

	OPTIONS[key] = value


def register_args(program : ArgumentParser) -> None:
	program.add_argument('--lip-syncer-model', help = wording.get('help.lip_syncer_model'), default = config.get_str_value('frame_processors.lip_syncer_model', 'wav2lip'), choices = frame_processors_choices.lip_syncer_models)


def apply_args(program : ArgumentParser) -> None:
	args = program.parse_args()
	frame_processors_globals.lip_syncer_model = args.lip_syncer_model


def pre_check() -> bool:
	if not facefusion.globals.skip_download:
		download_directory_path = resolve_relative_path('../.assets/models')
		model_url = get_options('model').get('url')
		conditional_download(download_directory_path, [ model_url ])
	return True


def post_check() -> bool:
	model_url = get_options('model').get('url')
	model_path = get_options('model').get('path')
	if not facefusion.globals.skip_download and not is_download_done(model_url, model_path):
		logger.error(wording.get('model_download_not_done') + wording.get('exclamation_mark'), NAME)
		return False
	elif not is_file(model_path):
		logger.error(wording.get('model_file_not_present') + wording.get('exclamation_mark'), NAME)
		return False
	return True


def pre_process(mode : ProcessMode) -> bool:
	audio_path = get_first_item(filter_audio_paths(facefusion.globals.source_paths))
	if not audio_path:
		logger.error(wording.get('select_audio_source') + wording.get('exclamation_mark'), NAME)
		return False
	if mode in [ 'output', 'preview' ] and not is_video(facefusion.globals.target_path):
		logger.error(wording.get('select_video_target') + wording.get('exclamation_mark'), NAME)
		return False
	if mode == 'output' and not facefusion.globals.output_path:
		logger.error(wording.get('select_file_or_directory_output') + wording.get('exclamation_mark'), NAME)
		return False
	return True


def post_process() -> None:
	read_static_image.cache_clear()
	read_static_audio.cache_clear()
	if facefusion.globals.video_memory_strategy == 'strict' or facefusion.globals.video_memory_strategy == 'moderate':
		clear_frame_processor()
	if facefusion.globals.video_memory_strategy == 'strict':
		clear_face_analyser()
		clear_content_analyser()
		clear_face_occluder()
		clear_face_parser()


def lip_sync(audio_frame : AudioFrame, target_face : Face, temp_frame : VisionFrame) -> VisionFrame:
	frame_processor = get_frame_processor()
	crop_frame, affine_matrix = warp_face_by_bbox(temp_frame, target_face.bbox, (96, 96))
	audio_frame = prepare_audio_frame(audio_frame)
	crop_frame = prepare_crop_frame(crop_frame)
	crop_frame = frame_processor.run(None,
	{
		'vid' : crop_frame,
		'mel' : audio_frame
	})[0]
	crop_frame = normalize_crop_frame(crop_frame)
	crop_mask = create_static_box_mask(crop_frame.shape[:2][::-1], 0.1, (50, 0, 0, 0))
	paste_frame = paste_back(temp_frame, crop_frame, crop_mask, affine_matrix)
	crop_mask_list = []
	if 'occlusion' in facefusion.globals.face_mask_types:
		temp_crop_frame, affine_matrix = warp_face_by_kps(temp_frame, target_face.kps, "ffhq_512", (512, 512))
		crop_mask_list.append(create_occlusion_mask(temp_crop_frame))
	if 'region' in facefusion.globals.face_mask_types:
		paste_crop_frame, affine_matrix = warp_face_by_kps(paste_frame, target_face.kps, "ffhq_512", (512, 512))
		crop_mask_list.append(create_region_mask(paste_crop_frame, facefusion.globals.face_mask_regions))
	if crop_mask_list:
		crop_mask = numpy.minimum.reduce(crop_mask_list)
		paste_frame = paste_back(temp_frame, crop_frame, crop_mask, affine_matrix)
	return paste_frame


def prepare_audio_frame(audio_frame : AudioFrame) -> AudioFrame:
	audio_frame = numpy.maximum(numpy.exp(-5 * numpy.log(10)), audio_frame)
	audio_frame = numpy.log10(audio_frame) * 1.6 + 3.2
	audio_frame = audio_frame.clip(-4, 4).astype(numpy.float32)
	audio_frame = numpy.expand_dims(audio_frame, axis = (0, 1))
	return audio_frame


def prepare_crop_frame(crop_frame : VisionFrame) -> VisionFrame:
	crop_frame = numpy.expand_dims(crop_frame, axis = 0)
	crop_frame_masked = crop_frame.copy()
	crop_frame_masked[:, 48:] = 0
	crop_frame_stack = numpy.concatenate((crop_frame_masked, crop_frame), axis = 3)
	crop_frame_stack = crop_frame_stack.transpose(0, 3, 1, 2).astype('float32') / 255.0
	return crop_frame_stack


def normalize_crop_frame(crop_frame : VisionFrame) -> VisionFrame:
	crop_frame = crop_frame[0].transpose(1, 2, 0)
	crop_frame = crop_frame.clip(0, 1) * 255
	crop_frame = crop_frame.astype(numpy.uint8)
	return crop_frame


def get_reference_frame(source_face : Face, target_face : Face, temp_frame : VisionFrame) -> VisionFrame:
	audio_path = get_first_item(filter_audio_paths(facefusion.globals.source_paths))
	audio_frame = get_audio_frame(audio_path, detect_video_fps(facefusion.globals.target_path), facefusion.globals.reference_frame_number)
	if audio_frame is not None:
		return lip_sync(audio_frame, target_face, temp_frame)
	return temp_frame


def process_frame(audio_frame : AudioFrame, reference_faces : FaceSet, temp_frame : VisionFrame) -> VisionFrame:
	if 'reference' in facefusion.globals.face_selector_mode:
		similar_faces = find_similar_faces(temp_frame, reference_faces, facefusion.globals.reference_face_distance)
		if similar_faces:
			for similar_face in similar_faces:
				temp_frame = lip_sync(audio_frame, similar_face, temp_frame)
	if 'one' in facefusion.globals.face_selector_mode:
		target_face = get_one_face(temp_frame)
		if target_face:
			temp_frame = lip_sync(audio_frame, target_face, temp_frame)
	if 'many' in facefusion.globals.face_selector_mode:
		many_faces = get_many_faces(temp_frame)
		if many_faces:
			for target_face in many_faces:
				temp_frame = lip_sync(audio_frame, target_face, temp_frame)
	return temp_frame


def process_frames(source_paths : List[str], temp_frame_paths : List[str], update_progress : Update_Process) -> None:
	reference_faces = get_reference_faces() if 'reference' in facefusion.globals.face_selector_mode else None
	source_audio_path = get_first_item(filter_audio_paths(source_paths))
	video_fps = detect_video_fps(facefusion.globals.target_path)
	for temp_frame_path in temp_frame_paths:
		frame_number = int(os.path.basename(temp_frame_path).split(".")[0])
		audio_frame = get_audio_frame(source_audio_path, video_fps, frame_number)
		if audio_frame is not None:
			temp_frame = read_image(temp_frame_path)
			result_frame = process_frame(audio_frame, reference_faces, temp_frame)
			write_image(temp_frame_path, result_frame)
		update_progress()


def process_image(source_paths : List[str], target_path : str, output_path : str) -> None:
	reference_faces = get_reference_faces() if 'reference' in facefusion.globals.face_selector_mode else None
	source_audio_path = get_first_item(filter_audio_paths(source_paths))
	audio_frame = get_audio_frame(source_audio_path, 25, 0)
	if audio_frame is not None:
		target_frame = read_static_image(target_path)
		result_frame = process_frame(audio_frame, reference_faces, target_frame)
		write_image(output_path, result_frame)


def process_video(source_paths : List[str], temp_frame_paths : List[str]) -> None:
	frame_processors.multi_process_frames(source_paths, temp_frame_paths, process_frames)
