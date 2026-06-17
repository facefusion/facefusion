import os
import tempfile
from typing import List

import numpy

from facefusion.filesystem import create_directory, is_directory, is_file, remove_directory
from facefusion.types import Face, FaceLandmarkSet, JobStatus


def is_test_job_file(file_path : str, job_status : JobStatus) -> bool:
	return is_file(get_test_job_file(file_path, job_status))


def get_test_job_file(file_path : str, job_status : JobStatus) -> str:
	return os.path.join(get_test_jobs_directory(), job_status, file_path)


def get_test_jobs_directory() -> str:
	return os.path.join(tempfile.gettempdir(), 'facefusion-test-jobs')


def get_test_example_file(file_path : str) -> str:
	return os.path.join(get_test_examples_directory(), file_path)


def get_test_examples_directory() -> str:
	return os.path.join(tempfile.gettempdir(), 'facefusion-test-examples')


def is_test_output_file(file_path : str) -> bool:
	return is_file(get_test_output_file(file_path))


def get_test_output_file(file_path : str) -> str:
	return os.path.join(get_test_outputs_directory(), file_path)


def get_test_outputs_directory() -> str:
	return os.path.join(tempfile.gettempdir(), 'facefusion-test-outputs')


def prepare_test_output_directory() -> bool:
	test_outputs_directory = get_test_outputs_directory()
	remove_directory(test_outputs_directory)
	create_directory(test_outputs_directory)
	return is_directory(test_outputs_directory)


def create_face_from_bounding_box(bounding_box : List[float]) -> Face:
	x1, y1, x2, y2 = bounding_box
	center_y = (y1 + y2) / 2
	face_landmark_5 = numpy.array(
	[
		[ x1, y1 ],
		[ x2, y1 ],
		[ x1, y2 ],
		[ x2, y2 ],
		[ (x1 + x2) / 2, center_y ]
	], dtype = numpy.float64)
	face_landmark_68 = numpy.zeros((68, 2), dtype = numpy.float64)
	face_landmark_68[0] = [ x1, center_y ]
	face_landmark_68[16] = [ x2, center_y ]
	landmark_set : FaceLandmarkSet =\
	{
		'5': face_landmark_5,
		'5/68': face_landmark_5,
		'68': face_landmark_68,
		'68/5': face_landmark_68
	}
	return Face(
		bounding_box = numpy.array(bounding_box, dtype = numpy.float64),
		score_set =\
		{
			'detector': 1.0,
			'landmarker': 1.0
		},
		landmark_set = landmark_set,
		angle = 0,
		embedding = numpy.zeros(512, dtype = numpy.float64),
		embedding_norm = numpy.zeros(512, dtype = numpy.float64),
		age = range(25, 30),
		gender = 'male',
		race = 'white'
	)
