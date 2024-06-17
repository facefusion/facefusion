import glob
import subprocess
import pytest

import facefusion.globals
from facefusion import process_manager
from facefusion.temp_helper import get_temp_directory_path, create_temp, clear_temp
from facefusion.download import conditional_download
from facefusion.ffmpeg import extract_frames, concat_video, read_audio_buffer
from .helper import get_test_examples_directory, prepare_test_output_directory, get_test_example_file, get_test_output_file


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('source.mp3'), get_test_example_file('source.wav') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vf', 'fps=25', get_test_example_file('target-240p-25fps.mp4') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vf', 'fps=30', get_test_example_file('target-240p-30fps.mp4') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vf', 'fps=60', get_test_example_file('target-240p-60fps.mp4') ])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	facefusion.globals.trim_frame_start = None
	facefusion.globals.trim_frame_end = None
	facefusion.globals.temp_frame_format = 'jpg'
	facefusion.globals.output_audio_encoder = 'aac'
	prepare_test_output_directory()


def test_extract_frames() -> None:
	target_paths =\
	[
		get_test_example_file('target-240p-25fps.mp4'),
		get_test_example_file('target-240p-30fps.mp4'),
		get_test_example_file('target-240p-60fps.mp4')
	]

	for target_path in target_paths:
		temp_directory_path = get_temp_directory_path(target_path)
		create_temp(target_path)

		assert extract_frames(target_path, '452x240', 30.0) is True
		assert len(glob.glob1(temp_directory_path, '*.jpg')) == 324

		clear_temp(target_path)


def test_extract_frames_with_trim_start() -> None:
	facefusion.globals.trim_frame_start = 224
	providers =\
	[
		(get_test_example_file('target-240p-25fps.mp4'), 55),
		(get_test_example_file('target-240p-30fps.mp4'), 100),
		(get_test_example_file('target-240p-60fps.mp4'), 212)
	]

	for target_path, frame_total in providers:
		temp_directory_path = get_temp_directory_path(target_path)
		create_temp(target_path)

		assert extract_frames(target_path, '452x240', 30.0) is True
		assert len(glob.glob1(temp_directory_path, '*.jpg')) == frame_total

		clear_temp(target_path)


def test_extract_frames_with_trim_start_and_trim_end() -> None:
	facefusion.globals.trim_frame_start = 124
	facefusion.globals.trim_frame_end = 224
	providers =\
	[
		(get_test_example_file('target-240p-25fps.mp4'), 120),
		(get_test_example_file('target-240p-30fps.mp4'), 100),
		(get_test_example_file('target-240p-60fps.mp4'), 50)
	]

	for target_path, frame_total in providers:
		temp_directory_path = get_temp_directory_path(target_path)
		create_temp(target_path)

		assert extract_frames(target_path, '452x240', 30.0) is True
		assert len(glob.glob1(temp_directory_path, '*.jpg')) == frame_total

		clear_temp(target_path)


def test_extract_frames_with_trim_end() -> None:
	facefusion.globals.trim_frame_end = 100
	providers =\
	[
		(get_test_example_file('target-240p-25fps.mp4'), 120),
		(get_test_example_file('target-240p-30fps.mp4'), 100),
		(get_test_example_file('target-240p-60fps.mp4'), 50)
	]

	for target_path, frame_total in providers:
		temp_directory_path = get_temp_directory_path(target_path)
		create_temp(target_path)

		assert extract_frames(target_path, '426x240', 30.0) is True
		assert len(glob.glob1(temp_directory_path, '*.jpg')) == frame_total

		clear_temp(target_path)


def test_concat_video() -> None:
	output_path = get_test_output_file('test-concat-video.mp4')
	temp_output_paths =\
	[
		get_test_example_file('target-240p.mp4'),
		get_test_example_file('target-240p.mp4')
	]

	assert concat_video(output_path, temp_output_paths) is True


def test_read_audio_buffer() -> None:
	assert isinstance(read_audio_buffer(get_test_example_file('source.mp3'), 1, 1), bytes)
	assert isinstance(read_audio_buffer(get_test_example_file('source.wav'), 1, 1), bytes)
	assert read_audio_buffer(get_test_example_file('invalid.mp3'), 1, 1) is None
