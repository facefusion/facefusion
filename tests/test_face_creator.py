import numpy
import pytest

from facefusion import face_classifier, face_detector, face_landmarker, face_recognizer, state_manager
from facefusion.download import conditional_download
from facefusion.face_analyser import get_many_faces, get_one_face
from facefusion.face_creator import interpolate_face, interpolate_points
from facefusion.face_store import clear_faces
from facefusion.vision import read_static_image
from .helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg'
	])

	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github' ])
	state_manager.init_item('face_detector_angles', [ 0 ])
	state_manager.init_item('face_detector_model', 'yolo_face')
	state_manager.init_item('face_detector_size', '640x640')
	state_manager.init_item('face_detector_margin', (0, 0, 0, 0))
	state_manager.init_item('face_detector_score', 0.5)
	state_manager.init_item('face_landmarker_model', 'many')
	state_manager.init_item('face_landmarker_score', 0.5)

	face_classifier.pre_check()
	face_detector.pre_check()
	face_landmarker.pre_check()
	face_recognizer.pre_check()


@pytest.fixture(autouse = True)
def before_each() -> None:
	face_classifier.clear_inference_pool()
	face_detector.clear_inference_pool()
	face_landmarker.clear_inference_pool()
	face_recognizer.clear_inference_pool()
	clear_faces()


def test_interpolate_face() -> None:
	source_frame = read_static_image(get_test_example_file('source.jpg'))
	face_before = get_one_face(get_many_faces([ source_frame ]))._replace(bounding_box = numpy.array([ 0, 0, 10, 10 ], dtype = numpy.float64))
	face_after = get_one_face(get_many_faces([ source_frame ]))._replace(bounding_box = numpy.array([ 80, 80, 90, 90 ], dtype = numpy.float64))

	assert interpolate_face(face_before, face_after, 0.5).bounding_box.tolist() == [ 40.0, 40.0, 50.0, 50.0 ]
	assert interpolate_face(face_before, face_after, 0.5).angle == face_after.angle
	assert interpolate_face(face_before, face_after, 0.5).embedding is face_after.embedding
	assert interpolate_face(face_before, face_after, 0.25).embedding is face_before.embedding


def test_interpolate_points() -> None:
	assert interpolate_points(numpy.array([0.0, 0.0]), numpy.array([10.0, 20.0]), 0.5).tolist() == [5.0, 10.0]
	assert interpolate_points(numpy.array([0.0, 0.0]), numpy.array([10.0, 20.0]), 0.0).tolist() == [0.0, 0.0]
	assert interpolate_points(numpy.array([0.0, 0.0]), numpy.array([10.0, 20.0]), 1.0).tolist() == [10.0, 20.0]
