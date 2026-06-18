import numpy
import pytest

from facefusion import face_classifier, face_detector, face_landmarker, face_recognizer, state_manager
from facefusion.download import conditional_download
from facefusion.face_analyser import get_many_faces, get_one_face
from facefusion.face_store import clear_faces
from facefusion.face_tracker import find_best_face_track, get_anchor_indices
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


def test_find_best_face_track() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	face = get_one_face(get_many_faces([ source_vision_frame ]))
	face_overlap = face._replace(bounding_box = numpy.array([ 12, 12, 52, 52 ]))
	face_distant = face._replace(bounding_box = numpy.array([ 200, 200, 240, 240 ]))
	face_track =\
	{
		0 : face._replace(bounding_box = numpy.array([ 10, 10, 50, 50 ]))
	}

	assert find_best_face_track([ face_track ], face_overlap, 1, 0.3) is face_track
	assert find_best_face_track([ face_track ], face_distant, 1, 0.3) == {}
	assert find_best_face_track([ face_track ], face_overlap, 0, 0.3) == {}


def test_get_anchor_indices() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	face = get_one_face(get_many_faces([ source_vision_frame ]))
	face_track =\
	{
		2 : face,
		8 : face
	}

	assert get_anchor_indices(face_track, 5) == (2, 8)
	assert get_anchor_indices(face_track, 1) == (-1, 2)
	assert get_anchor_indices(face_track, 9) == (8, -1)
