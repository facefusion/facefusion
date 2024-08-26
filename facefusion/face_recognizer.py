from typing import Tuple

import numpy

from facefusion import inference_manager
from facefusion.download import conditional_download_hashes, conditional_download_sources
from facefusion.face_helper import warp_face_by_face_landmark_5
from facefusion.filesystem import resolve_relative_path
from facefusion.thread_helper import conditional_thread_semaphore
from facefusion.typing import Embedding, FaceLandmark5, InferencePool, ModelOptions, ModelSet, VisionFrame

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
		},
		'template': 'arcface_112_v2',
		'size': (112, 112)
	}
}


def get_inference_pool() -> InferencePool:
	model_sources = get_model_options().get('sources')
	return inference_manager.get_inference_pool(__name__, model_sources)


def clear_inference_pool() -> None:
	inference_manager.clear_inference_pool(__name__)


def get_model_options() -> ModelOptions:
	return MODEL_SET.get('arcface')


def pre_check() -> bool:
	download_directory_path = resolve_relative_path('../.assets/models')
	model_hashes = get_model_options().get('hashes')
	model_sources = get_model_options().get('sources')

	return conditional_download_hashes(download_directory_path, model_hashes) and conditional_download_sources(download_directory_path, model_sources)


def calc_embedding(temp_vision_frame : VisionFrame, face_landmark_5 : FaceLandmark5) -> Tuple[Embedding, Embedding]:
	model_template = get_model_options().get('template')
	model_size = get_model_options().get('size')
	crop_vision_frame, matrix = warp_face_by_face_landmark_5(temp_vision_frame, face_landmark_5, model_template, model_size)
	crop_vision_frame = crop_vision_frame / 127.5 - 1
	crop_vision_frame = crop_vision_frame[:, :, ::-1].transpose(2, 0, 1).astype(numpy.float32)
	crop_vision_frame = numpy.expand_dims(crop_vision_frame, axis = 0)
	embedding = forward(crop_vision_frame)
	embedding = embedding.ravel()
	normed_embedding = embedding / numpy.linalg.norm(embedding)
	return embedding, normed_embedding


def forward(crop_vision_frame : VisionFrame) -> Embedding:
	face_recognizer = get_inference_pool().get('face_recognizer')

	with conditional_thread_semaphore():
		embedding = face_recognizer.run(None,
		{
			'input': crop_vision_frame
		})[0]

	return embedding
