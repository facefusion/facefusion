import subprocess

import numpy
import pytest

from facefusion import face_classifier, face_detector, face_landmarker, face_recognizer, state_manager
from facefusion.download import conditional_download
from facefusion.face_creator import average_face_geometry, get_many_faces, get_one_face, refill_faces
from facefusion.face_store import clear_faces
from facefusion.vision import read_static_image
from .helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg'
	])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('source.jpg'), '-vf', 'crop=iw*0.8:ih*0.8', get_test_example_file('source-80crop.jpg') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('source.jpg'), '-vf', 'crop=iw*0.7:ih*0.7', get_test_example_file('source-70crop.jpg') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('source.jpg'), '-vf', 'crop=iw*0.6:ih*0.6', get_test_example_file('source-60crop.jpg') ])

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


def test_get_one_face() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	face = get_one_face(get_many_faces([ source_vision_frame ]))

	assert face.bounding_box.size == 4


def test_get_many_faces() -> None:
	source_path = get_test_example_file('source.jpg')
	source_vision_frame = read_static_image(source_path)
	many_faces = get_many_faces([ source_vision_frame, source_vision_frame, source_vision_frame ])

	assert len(many_faces) == 3


def test_refill_faces() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	face = get_one_face(get_many_faces([ source_vision_frame ]))
	face_first = face._replace(bounding_box = numpy.array([ 0, 0, 10, 10 ]))
	face_middle = face._replace(bounding_box = numpy.array([ 40, 40, 50, 50 ]))
	face_last = face._replace(bounding_box = numpy.array([ 80, 80, 90, 90 ]))

	fill_faces = refill_faces([ face_first, None, face_last ])

	assert fill_faces[0].bounding_box.tolist() == [ 0.0, 0.0, 10.0, 10.0 ]
	assert fill_faces[1].bounding_box.tolist() == [ 40.0, 40.0, 50.0, 50.0 ]
	assert fill_faces[2].bounding_box.tolist() == [ 80.0, 80.0, 90.0, 90.0 ]

	fill_faces = refill_faces([ face_first, None, None, None, face_last ])

	assert fill_faces[0].bounding_box.tolist() == [ 0.0, 0.0, 10.0, 10.0 ]
	assert fill_faces[1].bounding_box.tolist() == [ 20.0, 20.0, 30.0, 30.0 ]
	assert fill_faces[2].bounding_box.tolist() == [ 40.0, 40.0, 50.0, 50.0 ]
	assert fill_faces[3].bounding_box.tolist() == [ 60.0, 60.0, 70.0, 70.0 ]
	assert fill_faces[4].bounding_box.tolist() == [ 80.0, 80.0, 90.0, 90.0 ]

	fill_faces = refill_faces([ face_first, None, face_middle, None, face_last ])

	assert fill_faces[0].bounding_box.tolist() == [ 0.0, 0.0, 10.0, 10.0 ]
	assert fill_faces[1].bounding_box.tolist() == [ 20.0, 20.0, 30.0, 30.0 ]
	assert fill_faces[2].bounding_box.tolist() == [ 40.0, 40.0, 50.0, 50.0 ]
	assert fill_faces[3].bounding_box.tolist() == [ 60.0, 60.0, 70.0, 70.0 ]
	assert fill_faces[4].bounding_box.tolist() == [ 80.0, 80.0, 90.0, 90.0 ]


def test_average_face_geometry() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	face_previous = get_one_face(get_many_faces([ source_vision_frame ]))
	face_next = get_one_face(get_many_faces([ source_vision_frame ]))
	face_previous = face_previous._replace(bounding_box = numpy.array([ 0, 0, 10, 10 ]))
	face_next = face_next._replace(bounding_box = numpy.array([ 80, 80, 90, 90 ]))

	assert average_face_geometry([face_previous, face_next], 0.5).bounding_box.tolist() == [40.0, 40.0, 50.0, 50.0]
	assert average_face_geometry([face_previous, face_next], 0.5).angle == face_next.angle
	assert average_face_geometry([face_previous, face_next], 0.5).embedding is face_next.embedding
	assert average_face_geometry([face_previous, face_next], 0.25).embedding is face_previous.embedding
