from typing import Any, List, Literal, Optional
from argparse import ArgumentParser
from time import sleep
import cv2
import numpy
import onnxruntime

import facefusion.globals
import facefusion.processors.frame.core as frame_processors
from facefusion import config, process_manager, logger, wording
from facefusion.execution import apply_execution_provider_options
from facefusion.face_analyser import get_one_face, get_many_faces, find_similar_faces, clear_face_analyser
from facefusion.face_masker import create_static_box_mask, create_occlusion_mask, create_mouth_mask, clear_face_occluder, clear_face_parser
from facefusion.face_helper import warp_face_by_face_landmark_5, warp_face_by_bounding_box, paste_back, create_bounding_box_from_face_landmark_68
from facefusion.face_store import get_reference_faces
from facefusion.content_analyser import clear_content_analyser
from facefusion.normalizer import normalize_output_path
from facefusion.thread_helper import thread_lock, conditional_thread_semaphore
from facefusion.typing import Face, VisionFrame, UpdateProgress, ProcessMode, ModelSet, OptionsWithModel, AudioFrame, QueuePayload
from facefusion.filesystem import is_file, has_audio, resolve_relative_path
from facefusion.download import conditional_download, is_download_done
from facefusion.audio import read_static_voice, get_voice_frame, create_empty_audio_frame
from facefusion.filesystem import is_image, is_video, filter_audio_paths
from facefusion.common_helper import get_first
from facefusion.vision import read_image, read_static_image, write_image, restrict_video_fps
from facefusion.processors.frame.typings import LipSyncerInputs
from facefusion.voice_extractor import clear_voice_extractor
from facefusion.processors.frame import globals as frame_processors_globals
from facefusion.processors.frame import choices as frame_processors_choices

FRAME_PROCESSOR = None
NAME = __name__.upper()
MODELS : ModelSet =\
{
	'wav2lip_gan':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/wav2lip_gan.onnx',
		'path': resolve_relative_path('../.assets/models/wav2lip_gan.onnx')
	}
}
OPTIONS : Optional[OptionsWithModel] = None


def get_frame_processor() -> Any:
	global FRAME_PROCESSOR

	with thread_lock():
		while process_manager.is_checking():
			sleep(0.5)
		if FRAME_PROCESSOR is None:
			model_path = get_options('model').get('path')
			FRAME_PROCESSOR = onnxruntime.InferenceSession(model_path, providers = apply_execution_provider_options(facefusion.globals.execution_device_id, facefusion.globals.execution_providers))
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
	program.add_argument('--lip-syncer-model', help = wording.get('help.lip_syncer_model'), default = config.get_str_value('frame_processors.lip_syncer_model', 'wav2lip_gan'), choices = frame_processors_choices.lip_syncer_models)


def apply_args(program : ArgumentParser) -> None:
	args = program.parse_args()
	frame_processors_globals.lip_syncer_model = args.lip_syncer_model


def pre_check() -> bool:
	download_directory_path = resolve_relative_path('../.assets/models')
	model_url = get_options('model').get('url')
	model_path = get_options('model').get('path')

	if not facefusion.globals.skip_download:
		process_manager.check()
		conditional_download(download_directory_path, [ model_url ])
		process_manager.end()
	return is_file(model_path)


def post_check() -> bool:
	model_url = get_options('model').get('url')
	model_path = get_options('model').get('path')

	if not facefusion.globals.skip_download and not is_download_done(model_url, model_path):
		logger.error(wording.get('model_download_not_done') + wording.get('exclamation_mark'), NAME)
		return False
	if not is_file(model_path):
		logger.error(wording.get('model_file_not_present') + wording.get('exclamation_mark'), NAME)
		return False
	return True


def pre_process(mode : ProcessMode) -> bool:
	if not has_audio(facefusion.globals.source_paths):
		logger.error(wording.get('select_audio_source') + wording.get('exclamation_mark'), NAME)
		return False
	if mode in [ 'output', 'preview' ] and not is_image(facefusion.globals.target_path) and not is_video(facefusion.globals.target_path):
		logger.error(wording.get('select_image_or_video_target') + wording.get('exclamation_mark'), NAME)
		return False
	if mode == 'output' and not normalize_output_path(facefusion.globals.target_path, facefusion.globals.output_path):
		logger.error(wording.get('select_file_or_directory_output') + wording.get('exclamation_mark'), NAME)
		return False
	return True


def post_process() -> None:
	read_static_image.cache_clear()
	read_static_voice.cache_clear()
	if facefusion.globals.video_memory_strategy == 'strict' or facefusion.globals.video_memory_strategy == 'moderate':
		clear_frame_processor()
	if facefusion.globals.video_memory_strategy == 'strict':
		clear_face_analyser()
		clear_content_analyser()
		clear_face_occluder()
		clear_face_parser()
		clear_voice_extractor()


def sync_lip(target_face : Face, temp_audio_frame : AudioFrame, temp_vision_frame : VisionFrame) -> VisionFrame:
	frame_processor = get_frame_processor()
	crop_mask_list = []
	temp_audio_frame = prepare_audio_frame(temp_audio_frame)
	crop_vision_frame, affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, target_face.landmarks.get('5/68'), 'ffhq_512', (512, 512))
	face_landmark_68 = cv2.transform(target_face.landmarks.get('68').reshape(1, -1, 2), affine_matrix).reshape(-1, 2)
	bounding_box = create_bounding_box_from_face_landmark_68(face_landmark_68)
	bounding_box[1] -= numpy.abs(bounding_box[3] - bounding_box[1]) * 0.125
	mouth_mask = create_mouth_mask(face_landmark_68)
	crop_mask_list.append(mouth_mask)
	box_mask = create_static_box_mask(crop_vision_frame.shape[:2][::-1], facefusion.globals.face_mask_blur, facefusion.globals.face_mask_padding)
	crop_mask_list.append(box_mask)

	if 'occlusion' in facefusion.globals.face_mask_types:
		occlusion_mask = create_occlusion_mask(crop_vision_frame)
		crop_mask_list.append(occlusion_mask)
	close_vision_frame, close_matrix = warp_face_by_bounding_box(crop_vision_frame, bounding_box, (96, 96))
	close_vision_frame = prepare_crop_frame(close_vision_frame)
	with conditional_thread_semaphore(facefusion.globals.execution_providers):
		close_vision_frame = frame_processor.run(None,
		{
			'source': temp_audio_frame,
			'target': close_vision_frame
		})[0]
	crop_vision_frame = normalize_crop_frame(close_vision_frame)
	crop_vision_frame = cv2.warpAffine(crop_vision_frame, cv2.invertAffineTransform(close_matrix), (512, 512), borderMode = cv2.BORDER_REPLICATE)
	crop_mask = numpy.minimum.reduce(crop_mask_list)
	paste_vision_frame = paste_back(temp_vision_frame, crop_vision_frame, crop_mask, affine_matrix)
	return paste_vision_frame


def prepare_audio_frame(temp_audio_frame : AudioFrame) -> AudioFrame:
	temp_audio_frame = numpy.maximum(numpy.exp(-5 * numpy.log(10)), temp_audio_frame)
	temp_audio_frame = numpy.log10(temp_audio_frame) * 1.6 + 3.2
	temp_audio_frame = temp_audio_frame.clip(-4, 4).astype(numpy.float32)
	temp_audio_frame = numpy.expand_dims(temp_audio_frame, axis = (0, 1))
	return temp_audio_frame


def prepare_crop_frame(crop_vision_frame : VisionFrame) -> VisionFrame:
	crop_vision_frame = numpy.expand_dims(crop_vision_frame, axis = 0)
	prepare_vision_frame = crop_vision_frame.copy()
	prepare_vision_frame[:, 48:] = 0
	crop_vision_frame = numpy.concatenate((prepare_vision_frame, crop_vision_frame), axis = 3)
	crop_vision_frame = crop_vision_frame.transpose(0, 3, 1, 2).astype('float32') / 255.0
	return crop_vision_frame


def normalize_crop_frame(crop_vision_frame : VisionFrame) -> VisionFrame:
	crop_vision_frame = crop_vision_frame[0].transpose(1, 2, 0)
	crop_vision_frame = crop_vision_frame.clip(0, 1) * 255
	crop_vision_frame = crop_vision_frame.astype(numpy.uint8)
	return crop_vision_frame


def get_reference_frame(source_face : Face, target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	pass


def process_frame(inputs : LipSyncerInputs) -> VisionFrame:
	reference_faces = inputs.get('reference_faces')
	source_audio_frame = inputs.get('source_audio_frame')
	target_vision_frame = inputs.get('target_vision_frame')

	if facefusion.globals.face_selector_mode == 'many':
		many_faces = get_many_faces(target_vision_frame)
		if many_faces:
			for target_face in many_faces:
				target_vision_frame = sync_lip(target_face, source_audio_frame, target_vision_frame)
	if facefusion.globals.face_selector_mode == 'one':
		target_face = get_one_face(target_vision_frame)
		if target_face:
			target_vision_frame = sync_lip(target_face, source_audio_frame, target_vision_frame)
	if facefusion.globals.face_selector_mode == 'reference':
		similar_faces = find_similar_faces(reference_faces, target_vision_frame, facefusion.globals.reference_face_distance)
		if similar_faces:
			for similar_face in similar_faces:
				target_vision_frame = sync_lip(similar_face, source_audio_frame, target_vision_frame)
	return target_vision_frame


def process_frames(source_paths : List[str], queue_payloads : List[QueuePayload], update_progress : UpdateProgress) -> None:
	reference_faces = get_reference_faces() if 'reference' in facefusion.globals.face_selector_mode else None
	source_audio_path = get_first(filter_audio_paths(source_paths))
	temp_video_fps = restrict_video_fps(facefusion.globals.target_path, facefusion.globals.output_video_fps)

	for queue_payload in process_manager.manage(queue_payloads):
		frame_number = queue_payload['frame_number']
		target_vision_path = queue_payload['frame_path']
		source_audio_frame = get_voice_frame(source_audio_path, temp_video_fps, frame_number)
		if not numpy.any(source_audio_frame):
			source_audio_frame = create_empty_audio_frame()
		target_vision_frame = read_image(target_vision_path)
		output_vision_frame = process_frame(
		{
			'reference_faces': reference_faces,
			'source_audio_frame': source_audio_frame,
			'target_vision_frame': target_vision_frame
		})
		write_image(target_vision_path, output_vision_frame)
		update_progress(1)


def process_image(source_paths : List[str], target_path : str, output_path : str) -> None:
	reference_faces = get_reference_faces() if 'reference' in facefusion.globals.face_selector_mode else None
	source_audio_frame = create_empty_audio_frame()
	target_vision_frame = read_static_image(target_path)
	output_vision_frame = process_frame(
	{
		'reference_faces': reference_faces,
		'source_audio_frame': source_audio_frame,
		'target_vision_frame': target_vision_frame
	})
	write_image(output_path, output_vision_frame)


def process_video(source_paths : List[str], temp_frame_paths : List[str]) -> None:
	source_audio_paths = filter_audio_paths(facefusion.globals.source_paths)
	temp_video_fps = restrict_video_fps(facefusion.globals.target_path, facefusion.globals.output_video_fps)
	for source_audio_path in source_audio_paths:
		read_static_voice(source_audio_path, temp_video_fps)
	frame_processors.multi_process_frames(source_paths, temp_frame_paths, process_frames)
