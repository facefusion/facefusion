from typing import Tuple

import numpy

from facefusion import inference_manager
from facefusion.download import conditional_download_hashes, conditional_download_sources
from facefusion.face_helper import warp_face_by_face_landmark_5
from facefusion.filesystem import resolve_relative_path
from facefusion.thread_helper import conditional_thread_semaphore
from facefusion.typing import FaceLandmark5, InferencePool, ModelOptions, ModelSet, Prediction, VisionFrame

MODEL_SET : ModelSet =\
{
	'fair_face':
	{
		'hashes':
		{
			'gender_age':
			{
				'url': 'https://huggingface.co/bluefoxcreation/gender_age/resolve/main/fair_face.hash',
				'path': resolve_relative_path('../.assets/models/fair_face.hash')
			}
		},
		'sources':
		{
			'gender_age':
			{
				'url': 'https://huggingface.co/bluefoxcreation/gender_age/resolve/main/fair_face.onnx',
				'path': resolve_relative_path('../.assets/models/fair_face.onnx')
			}
		},
		'template': 'arcface_112_v2',
		'size': (224, 224),
		'mean': [ 0.485, 0.456, 0.406 ],
		'standard_deviation': [ 0.229, 0.224, 0.225 ]
	}
}


def categorize_age(age : int) -> str:
	if age < 2:
		return 'child'
	elif age < 3:
		return 'teen'
	elif age < 7:
		return 'adult'
	return 'senior'


def categorize_gender(gender : int) -> str:
	if gender:
		return 'female'
	return 'male'


def categorize_race(race : int) -> str:
	if race == 0:
		return 'white'
	elif race == 1:
		return 'black'
	elif race == 2:
		return 'latino'
	elif race == 3 or race == 4:
		return 'asian'
	elif race == 5:
		return 'indian'
	return 'arabic'


def get_inference_pool() -> InferencePool:
	model_sources = get_model_options().get('sources')
	return inference_manager.get_inference_pool(__name__, model_sources)


def clear_inference_pool() -> None:
	inference_manager.clear_inference_pool(__name__)


def get_model_options() -> ModelOptions:
	return MODEL_SET.get('fair_face')


def pre_check() -> bool:
	download_directory_path = resolve_relative_path('../.assets/models')
	model_hashes = get_model_options().get('hashes')
	model_sources = get_model_options().get('sources')

	return conditional_download_hashes(download_directory_path, model_hashes) and conditional_download_sources(download_directory_path, model_sources)


def detect_gender_age(temp_vision_frame : VisionFrame, face_landmark_5 : FaceLandmark5) -> Tuple[str, str, str]:
	model_template = get_model_options().get('template')
	model_size = get_model_options().get('size')
	model_mean = get_model_options().get('mean')
	model_standard_deviation = get_model_options().get('standard_deviation')
	crop_vision_frame, _ = warp_face_by_face_landmark_5(temp_vision_frame, face_landmark_5, model_template, model_size)
	crop_vision_frame = crop_vision_frame.astype(numpy.float32)[:, :, ::-1] / 255
	crop_vision_frame -= model_mean
	crop_vision_frame /= model_standard_deviation
	crop_vision_frame = crop_vision_frame.transpose(2, 0, 1)
	crop_vision_frame = numpy.expand_dims(crop_vision_frame, axis=0)
	gender_raw, age_raw, race_raw = forward(crop_vision_frame)
	gender = categorize_gender(int(gender_raw[0]))
	age = categorize_age(int(age_raw[0]))
	race = categorize_race(int(race_raw[0]))
	return gender, age, race


def forward(crop_vision_frame : VisionFrame) -> Tuple[Prediction, Prediction, Prediction]:
	gender_age = get_inference_pool().get('gender_age')

	with conditional_thread_semaphore():
		race_raw, gender_raw, age_raw = gender_age.run(None,
		{
			'input': crop_vision_frame
		})

	return gender_raw, age_raw, race_raw
