import numpy
import pytest

from facefusion import face_classifier, face_detector, face_landmarker, face_recognizer, state_manager
from facefusion.download import conditional_download
from facefusion.face_creator import get_many_faces, get_one_face
from facefusion.face_store import clear_faces, get_faces, resolve_lock, set_faces
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
	state_manager.init_item('face_detector_model', 'many')
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


def test_set_and_get_faces() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	face = get_one_face(get_many_faces([ source_vision_frame ]))
	vision_frame = numpy.ones((64, 64, 3), dtype = numpy.uint8)

	assert get_faces(vision_frame) is None

	set_faces(vision_frame, [ face ])

	assert get_faces(vision_frame) == [ face ]


def test_empty_frame_returns_none() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	face = get_one_face(get_many_faces([ source_vision_frame ]))
	empty_vision_frame = numpy.zeros((64, 64, 3), dtype = numpy.uint8)

	set_faces(empty_vision_frame, [ face ])

	assert get_faces(empty_vision_frame) is None


def test_resolve_lock_is_stable() -> None:
	vision_frame = numpy.ones((64, 64, 3), dtype = numpy.uint8)
	other_vision_frame = numpy.full((64, 64, 3), 2, dtype = numpy.uint8)
	empty_vision_frame = numpy.zeros((64, 64, 3), dtype = numpy.uint8)

	assert resolve_lock(vision_frame) is resolve_lock(vision_frame)
	assert resolve_lock(vision_frame) is not resolve_lock(other_vision_frame)
	assert resolve_lock(empty_vision_frame) is not resolve_lock(empty_vision_frame)


def test_clear_faces() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	face = get_one_face(get_many_faces([ source_vision_frame ]))
	vision_frame = numpy.ones((64, 64, 3), dtype = numpy.uint8)

	set_faces(vision_frame, [ face ])
	clear_faces()

	assert get_faces(vision_frame) is None
