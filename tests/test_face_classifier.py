import pytest

from facefusion import face_classifier, face_detector, inference_manager, process_manager, state_manager
from facefusion.download import conditional_download
from facefusion.face_classifier import categorize_age, categorize_gender, categorize_race, classify_face
from facefusion.face_detector import detect_with_yolo_face
from facefusion.vision import read_static_image
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	inference_manager.init()

	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg'
	])

	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github' ])
	state_manager.init_item('face_detector_model', 'yolo_face')
	state_manager.init_item('face_detector_score', 0.5)

	face_classifier.pre_check()
	face_detector.pre_check()


@pytest.fixture(autouse = True)
def before_each() -> None:
	face_classifier.clear_inference_pool()


def test_classify_face() -> None:
	source_frame = read_static_image(get_test_example_file('source.jpg'))
	_, _, face_landmarks_5 = detect_with_yolo_face(source_frame, '640x640')

	assert classify_face(source_frame, face_landmarks_5[0]) == ('female', range(20, 29), 'white')


def test_categorize_gender() -> None:
	assert categorize_gender(0) == 'male'
	assert categorize_gender(1) == 'female'


def test_categorize_age() -> None:
	assert categorize_age(0) == range(0, 2)
	assert categorize_age(1) == range(3, 9)
	assert categorize_age(2) == range(10, 19)
	assert categorize_age(3) == range(20, 29)
	assert categorize_age(4) == range(30, 39)
	assert categorize_age(5) == range(40, 49)
	assert categorize_age(6) == range(50, 59)
	assert categorize_age(7) == range(60, 69)
	assert categorize_age(8) == range(70, 100)


def test_categorize_race() -> None:
	assert categorize_race(0) == 'white'
	assert categorize_race(1) == 'black'
	assert categorize_race(2) == 'latino'
	assert categorize_race(3) == 'asian'
	assert categorize_race(4) == 'asian'
	assert categorize_race(5) == 'indian'
	assert categorize_race(6) == 'arabic'
