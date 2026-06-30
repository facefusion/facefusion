import subprocess

import pytest

from facefusion import face_detector, state_manager
from facefusion.download import conditional_download
from facefusion.face_detector import detect_with_retinaface, detect_with_scrfd, detect_with_yolo_face, detect_with_yunet
from facefusion.face_helper import apply_nms, get_nms_threshold
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
	state_manager.init_item('face_detector_score', 0.5)

	face_detector.pre_check()


@pytest.fixture(autouse = True)
def before_each() -> None:
	face_detector.clear_inference_pool()


def test_detect_with_retinaface() -> None:
	source_paths =\
	[
		get_test_example_file('source.jpg'),
		get_test_example_file('source-80crop.jpg'),
		get_test_example_file('source-70crop.jpg'),
		get_test_example_file('source-60crop.jpg')
	]

	for source_path in source_paths:
		source_frame = read_static_image(source_path)
		bounding_boxes, face_scores, face_landmarks_5 = detect_with_retinaface(source_frame, '320x320')
		keep_indices = apply_nms(bounding_boxes, face_scores, 0.5, get_nms_threshold('retinaface', [ 0 ]))

		assert len(keep_indices) == 1


def test_detect_with_scrfd() -> None:
	source_paths =\
	[
		get_test_example_file('source.jpg'),
		get_test_example_file('source-80crop.jpg'),
		get_test_example_file('source-70crop.jpg'),
		get_test_example_file('source-60crop.jpg')
	]

	for source_path in source_paths:
		source_frame = read_static_image(source_path)
		bounding_boxes, face_scores, face_landmarks_5 = detect_with_scrfd(source_frame, '320x320')
		keep_indices = apply_nms(bounding_boxes, face_scores, 0.5, get_nms_threshold('scrfd', [ 0 ]))

		assert len(keep_indices) == 1


def test_detect_with_yolo_face() -> None:
	source_paths =\
	[
		get_test_example_file('source.jpg'),
		get_test_example_file('source-80crop.jpg'),
		get_test_example_file('source-70crop.jpg'),
		get_test_example_file('source-60crop.jpg')
	]

	for source_path in source_paths:
		source_frame = read_static_image(source_path)
		bounding_boxes, face_scores, face_landmarks_5 = detect_with_yolo_face(source_frame, '640x640')
		keep_indices = apply_nms(bounding_boxes, face_scores, 0.5, get_nms_threshold('yolo_face', [ 0 ]))

		assert len(keep_indices) == 1


def test_detect_with_yunet() -> None:
	source_paths =\
	[
		get_test_example_file('source.jpg'),
		get_test_example_file('source-80crop.jpg'),
		get_test_example_file('source-70crop.jpg'),
		get_test_example_file('source-60crop.jpg')
	]

	for source_path in source_paths:
		source_frame = read_static_image(source_path)
		bounding_boxes, face_scores, face_landmarks_5 = detect_with_yunet(source_frame, '640x640')
		keep_indices = apply_nms(bounding_boxes, face_scores, 0.5, get_nms_threshold('yunet', [ 0 ]))

		assert len(keep_indices) == 1
