from time import sleep
from typing import Optional, Tuple

import numpy

from facefusion import process_manager, state_manager
from facefusion.download import conditional_download_hashes, conditional_download_sources
from facefusion.execution import create_inference_pool
from facefusion.face_helper import warp_face_by_translation
from facefusion.filesystem import resolve_relative_path
from facefusion.thread_helper import conditional_thread_semaphore, thread_lock
from facefusion.typing import BoundingBox, InferencePool, ModelOptions, ModelSet, VisionFrame

INFERENCE_POOL : Optional[InferencePool] = None
MODEL_SET : ModelSet =\
{
	'gender_age':
	{
		'hashes':
		{
			'gender_age':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/gender_age.hash',
				'path': resolve_relative_path('../.assets/models/gender_age.hash')
			}
		},
		'sources':
		{
			'gender_age':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/gender_age.onnx',
				'path': resolve_relative_path('../.assets/models/gender_age.onnx')
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
	return MODEL_SET.get('gender_age')


def pre_check() -> bool:
	download_directory_path = resolve_relative_path('../.assets/models')
	model_hashes = get_model_options().get('hashes')
	model_sources = get_model_options().get('sources')

	return conditional_download_hashes(download_directory_path, model_hashes) and conditional_download_sources(download_directory_path, model_sources)


def detect_gender_age(temp_vision_frame : VisionFrame, bounding_box : BoundingBox) -> Tuple[int, int]:
	gender_age = get_inference_pool().get('gender_age')
	bounding_box = bounding_box.reshape(2, -1)
	scale = 64 / numpy.subtract(*bounding_box[::-1]).max()
	translation = 48 - bounding_box.sum(axis = 0) * scale * 0.5
	crop_vision_frame, affine_matrix = warp_face_by_translation(temp_vision_frame, translation, scale, (96, 96))
	crop_vision_frame = crop_vision_frame[:, :, ::-1].transpose(2, 0, 1).astype(numpy.float32)
	crop_vision_frame = numpy.expand_dims(crop_vision_frame, axis = 0)

	with conditional_thread_semaphore():
		prediction = gender_age.run(None,
		{
			'input': crop_vision_frame
		})[0][0]

	gender = int(numpy.argmax(prediction[:2]))
	age = int(numpy.round(prediction[2] * 100))
	return gender, age
