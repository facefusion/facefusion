import subprocess
import pytest

import facefusion.globals
from facefusion.download import conditional_download
from facefusion.face_analyser import pre_check, clear_face_analyser, get_one_face
from facefusion.typing import Face
from facefusion.vision import read_static_image


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download('.assets/examples',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.jpg'
	])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/source.jpg', '-vf', 'crop=iw*0.8:ih*0.8', '.assets/examples/source-80crop.jpg' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/source.jpg', '-vf', 'crop=iw*0.7:ih*0.7', '.assets/examples/source-70crop.jpg' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/source.jpg', '-vf', 'crop=iw*0.6:ih*0.6', '.assets/examples/source-60crop.jpg' ])


@pytest.fixture(autouse = True)
def before_each() -> None:
	facefusion.globals.face_detector_score = 0.5
	facefusion.globals.face_landmarker_score = 0.5
	facefusion.globals.face_recognizer_model = 'arcface_inswapper'
	clear_face_analyser()


def test_get_one_face_with_retinaface() -> None:
	facefusion.globals.face_detector_model = 'retinaface'
	facefusion.globals.face_detector_size = '320x320'

	pre_check()
	source_paths =\
	[
		'.assets/examples/source.jpg',
		'.assets/examples/source-80crop.jpg',
		'.assets/examples/source-70crop.jpg',
		'.assets/examples/source-60crop.jpg'
	]
	for source_path in source_paths:
		source_frame = read_static_image(source_path)
		face = get_one_face(source_frame)

		assert isinstance(face, Face)


def test_get_one_face_with_scrfd() -> None:
	facefusion.globals.face_detector_model = 'scrfd'
	facefusion.globals.face_detector_size = '640x640'

	pre_check()
	source_paths =\
	[
		'.assets/examples/source.jpg',
		'.assets/examples/source-80crop.jpg',
		'.assets/examples/source-70crop.jpg',
		'.assets/examples/source-60crop.jpg'
	]
	for source_path in source_paths:
		source_frame = read_static_image(source_path)
		face = get_one_face(source_frame)

		assert isinstance(face, Face)


def test_get_one_face_with_yoloface() -> None:
	facefusion.globals.face_detector_model = 'yoloface'
	facefusion.globals.face_detector_size = '640x640'

	pre_check()
	source_paths =\
	[
		'.assets/examples/source.jpg',
		'.assets/examples/source-80crop.jpg',
		'.assets/examples/source-70crop.jpg',
		'.assets/examples/source-60crop.jpg'
	]
	for source_path in source_paths:
		source_frame = read_static_image(source_path)
		face = get_one_face(source_frame)

		assert isinstance(face, Face)


def test_get_one_face_with_yunet() -> None:
	facefusion.globals.face_detector_model = 'yunet'
	facefusion.globals.face_detector_size = '640x640'

	pre_check()
	source_paths =\
	[
		'.assets/examples/source.jpg',
		'.assets/examples/source-80crop.jpg',
		'.assets/examples/source-70crop.jpg',
		'.assets/examples/source-60crop.jpg'
	]
	for source_path in source_paths:
		source_frame = read_static_image(source_path)
		face = get_one_face(source_frame)

		assert isinstance(face, Face)
