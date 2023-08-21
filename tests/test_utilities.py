import glob
import subprocess
import pytest

import facefusion.globals
from facefusion.utilities import conditional_download, detect_fps, extract_frames, create_temp, get_temp_directory_path, clear_temp


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	facefusion.globals.temp_frame_quality = 100
	facefusion.globals.trim_frame_start = None
	facefusion.globals.trim_frame_end = None
	facefusion.globals.temp_frame_format = 'png'
	conditional_download('.assets/examples',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vf', 'fps=25', '.assets/examples/target-240p-25fps.mp4' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vf', 'fps=30', '.assets/examples/target-240p-30fps.mp4' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vf', 'fps=60', '.assets/examples/target-240p-60fps.mp4' ])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	facefusion.globals.trim_frame_start = None
	facefusion.globals.trim_frame_end = None
	facefusion.globals.temp_frame_quality = 90
	facefusion.globals.temp_frame_format = 'jpg'


def test_detect_fps() -> None:
	assert detect_fps('.assets/examples/target-240p-25fps.mp4') == 25.0
	assert detect_fps('.assets/examples/target-240p-30fps.mp4') == 30.0
	assert detect_fps('.assets/examples/target-240p-60fps.mp4') == 60.0


def test_extract_frames() -> None:
	target_paths =\
	[
		'.assets/examples/target-240p-25fps.mp4',
		'.assets/examples/target-240p-30fps.mp4',
		'.assets/examples/target-240p-60fps.mp4'
	]
	for target_path in target_paths:
		temp_directory_path = get_temp_directory_path(target_path)
		create_temp(target_path)

		assert extract_frames(target_path, 30) is True
		assert len(glob.glob1(temp_directory_path, '*.jpg')) == 324

		clear_temp(target_path)


def test_extract_frames_with_trim_start() -> None:
	facefusion.globals.trim_frame_start = 224
	data_provider =\
	[
		('.assets/examples/target-240p-25fps.mp4', 55),
		('.assets/examples/target-240p-30fps.mp4', 100),
		('.assets/examples/target-240p-60fps.mp4', 212)
	]
	for target_path, frame_total in data_provider:
		temp_directory_path = get_temp_directory_path(target_path)
		create_temp(target_path)

		assert extract_frames(target_path, 30) is True
		assert len(glob.glob1(temp_directory_path, '*.jpg')) == frame_total

		clear_temp(target_path)


def test_extract_frames_with_trim_start_and_trim_end() -> None:
	facefusion.globals.trim_frame_start = 224
	facefusion.globals.trim_frame_end = 324
	data_provider =\
	[
		('.assets/examples/target-240p-25fps.mp4', 55),
		('.assets/examples/target-240p-30fps.mp4', 100),
		('.assets/examples/target-240p-60fps.mp4', 50)
	]
	for target_path, frame_total in data_provider:
		temp_directory_path = get_temp_directory_path(target_path)
		create_temp(target_path)

		assert extract_frames(target_path, 30) is True
		assert len(glob.glob1(temp_directory_path, '*.jpg')) == frame_total

		clear_temp(target_path)


def test_extract_frames_with_trim_end() -> None:
	facefusion.globals.trim_frame_end = 100
	data_provider =\
	[
		('.assets/examples/target-240p-25fps.mp4', 120),
		('.assets/examples/target-240p-30fps.mp4', 100),
		('.assets/examples/target-240p-60fps.mp4', 50)
	]
	for target_path, frame_total in data_provider:
		temp_directory_path = get_temp_directory_path(target_path)
		create_temp(target_path)

		assert extract_frames(target_path, 30) is True
		assert len(glob.glob1(temp_directory_path, '*.jpg')) == frame_total

		clear_temp(target_path)
