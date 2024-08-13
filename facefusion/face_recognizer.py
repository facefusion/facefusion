from time import sleep
from typing import Optional, Tuple

import numpy

from facefusion import process_manager, state_manager
from facefusion.download import conditional_download_hashes, conditional_download_sources
from facefusion.execution import create_inference_pool
from facefusion.face_helper import warp_face_by_face_landmark_5
from facefusion.filesystem import resolve_relative_path
from facefusion.thread_helper import conditional_thread_semaphore, thread_lock
from facefusion.typing import Embedding, FaceLandmark5, InferencePool, ModelOptions, ModelSet, VisionFrame

INFERENCE_POOL : Optional[InferencePool] = None
MODEL_SET : ModelSet =\
{
	'arcface':
	{
		'hashes':
		{
			'face_recognizer':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/arcface_w600k_r50.hash',
				'path': resolve_relative_path('../.assets/models/arcface_w600k_r50.hash')
			}
		},
		'sources':
		{
			'face_recognizer':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/arcface_w600k_r50.onnx',
				'path': resolve_relative_path('../.assets/models/arcface_w600k_r50.onnx')
			}
		}
	}
}


def get_inference_pool() -> InferencePool:
	global INFERENCE_POOL

	with thread_lock():
		while process_manager.is_checking():
			sleep(0.5)
		if INFERENCE_POOL is None:
			model_sources = get_model_options().get('sources')
			INFERENCE_POOL = create_inference_pool(model_sources, state_manager.get_item('execution_device_id'), state_manager.get_item('execution_providers'))
		return INFERENCE_POOL


def clear_inference_pool() -> None:
	global INFERENCE_POOL

	INFERENCE_POOL = None


def get_model_options() -> ModelOptions:
	return MODEL_SET.get('arcface')


def pre_check() -> bool:
	download_directory_path = resolve_relative_path('../.assets/models')
	model_hashes = get_model_options().get('hashes')
	model_sources = get_model_options().get('sources')

	return conditional_download_hashes(download_directory_path, model_hashes) and conditional_download_sources(download_directory_path, model_sources)


def calc_embedding(temp_vision_frame : VisionFrame, face_landmark_5 : FaceLandmark5) -> Tuple[Embedding, Embedding]:
	face_recognizer = get_inference_pool().get('face_recognizer')
	crop_vision_frame, matrix = warp_face_by_face_landmark_5(temp_vision_frame, face_landmark_5, 'arcface_112_v2', (112, 112))
	crop_vision_frame = crop_vision_frame / 127.5 - 1
	crop_vision_frame = crop_vision_frame[:, :, ::-1].transpose(2, 0, 1).astype(numpy.float32)
	crop_vision_frame = numpy.expand_dims(crop_vision_frame, axis = 0)

	with conditional_thread_semaphore():
		embedding = face_recognizer.run(None,
		{
			'input': crop_vision_frame
		})[0]

	embedding = embedding.ravel()
	normed_embedding = embedding / numpy.linalg.norm(embedding)
	return embedding, normed_embedding
