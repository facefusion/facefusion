from functools import lru_cache
from typing import List, Tuple

import numpy

from facefusion import inference_manager
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.face_helper import warp_face_by_face_landmark_5
from facefusion.filesystem import resolve_relative_path
from facefusion.thread_helper import conditional_thread_semaphore
from facefusion.types import Age, DownloadScope, FaceLandmark5, Gender, InferencePool, ModelOptions, ModelSet, Race, VisionFrame


@lru_cache(maxsize = None)
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
	return\
	{
		'fairface':
		{
			'hashes':
			{
				'face_classifier':
				{
					'url': resolve_download_url('models-3.0.0', 'fairface.hash'),
					'path': resolve_relative_path('../.assets/models/fairface.hash')
				}
			},
			'sources':
			{
				'face_classifier':
				{
					'url': resolve_download_url('models-3.0.0', 'fairface.onnx'),
					'path': resolve_relative_path('../.assets/models/fairface.onnx')
				}
			},
			'template': 'arcface_112_v2',
			'size': (224, 224),
			'mean': [ 0.485, 0.456, 0.406 ],
			'standard_deviation': [ 0.229, 0.224, 0.225 ]
		}
	}


def get_inference_pool() -> InferencePool:
	model_names = [ 'fairface' ]
	model_source_set = get_model_options().get('sources')

	return inference_manager.get_inference_pool(__name__, model_names, model_source_set)


def clear_inference_pool() -> None:
	model_names = [ 'fairface' ]
	inference_manager.clear_inference_pool(__name__, model_names)


def get_model_options() -> ModelOptions:
	return create_static_model_set('full').get('fairface')


def pre_check() -> bool:
	model_hash_set = get_model_options().get('hashes')
	model_source_set = get_model_options().get('sources')

	return conditional_download_hashes(model_hash_set) and conditional_download_sources(model_source_set)


def classify_face(temp_vision_frame : VisionFrame, face_landmark_5 : FaceLandmark5) -> Tuple[Gender, Age, Race]:
	model_template = get_model_options().get('template')
	model_size = get_model_options().get('size')
	model_mean = get_model_options().get('mean')
	model_standard_deviation = get_model_options().get('standard_deviation')
	crop_vision_frame, _ = warp_face_by_face_landmark_5(temp_vision_frame, face_landmark_5, model_template, model_size)
	crop_vision_frame = crop_vision_frame.astype(numpy.float32)[:, :, ::-1] / 255.0
	crop_vision_frame -= model_mean
	crop_vision_frame /= model_standard_deviation
	crop_vision_frame = crop_vision_frame.transpose(2, 0, 1)
	crop_vision_frame = numpy.expand_dims(crop_vision_frame, axis = 0)
	gender_id, age_id, race_id = forward(crop_vision_frame)
	gender = categorize_gender(gender_id[0])
	age = categorize_age(age_id[0])
	race = categorize_race(race_id[0])
	return gender, age, race


def forward(crop_vision_frame : VisionFrame) -> Tuple[List[int], List[int], List[int]]:
	face_classifier = get_inference_pool().get('face_classifier')

	with conditional_thread_semaphore():
		race_id, gender_id, age_id = face_classifier.run(None,
		{
			'input': crop_vision_frame
		})

	return gender_id, age_id, race_id


def categorize_gender(gender_id : int) -> Gender:
	if gender_id == 1:
		return 'female'
	return 'male'


def categorize_age(age_id : int) -> Age:
	if age_id == 0:
		return range(0, 2)
	if age_id == 1:
		return range(3, 9)
	if age_id == 2:
		return range(10, 19)
	if age_id == 3:
		return range(20, 29)
	if age_id == 4:
		return range(30, 39)
	if age_id == 5:
		return range(40, 49)
	if age_id == 6:
		return range(50, 59)
	if age_id == 7:
		return range(60, 69)
	return range(70, 100)


def categorize_race(race_id : int) -> Race:
	if race_id == 1:
		return 'black'
	if race_id == 2:
		return 'latino'
	if race_id == 3 or race_id == 4:
		return 'asian'
	if race_id == 5:
		return 'indian'
	if race_id == 6:
		return 'arabic'
	return 'white'
