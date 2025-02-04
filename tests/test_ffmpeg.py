<<<<<<< HEAD
import glob
import subprocess
import pytest

import facefusion.globals
from facefusion import process_manager
from facefusion.filesystem import get_temp_directory_path, create_temp, clear_temp
from facefusion.download import conditional_download
from facefusion.ffmpeg import extract_frames, read_audio_buffer
=======
import subprocess
import tempfile

import pytest

from facefusion import process_manager, state_manager
from facefusion.download import conditional_download
from facefusion.ffmpeg import concat_video, extract_frames, read_audio_buffer, replace_audio, restore_audio
from facefusion.filesystem import copy_file
from facefusion.temp_helper import clear_temp_directory, create_temp_directory, get_temp_file_path, get_temp_frame_paths
from .helper import get_test_example_file, get_test_examples_directory, get_test_output_file, prepare_test_output_directory
>>>>>>> origin/master


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	process_manager.start()
<<<<<<< HEAD
	conditional_download('.assets/examples',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/source.mp3', '.assets/examples/source.wav' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vf', 'fps=25', '.assets/examples/target-240p-25fps.mp4' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vf', 'fps=30', '.assets/examples/target-240p-30fps.mp4' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vf', 'fps=60', '.assets/examples/target-240p-60fps.mp4' ])
=======
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('source.mp3'), get_test_example_file('source.wav') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vf', 'fps=25', get_test_example_file('target-240p-25fps.mp4') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vf', 'fps=30', get_test_example_file('target-240p-30fps.mp4') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vf', 'fps=60', get_test_example_file('target-240p-60fps.mp4') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('source.mp3'), '-i', get_test_example_file('target-240p.mp4'), '-ar', '16000', get_test_example_file('target-240p-16khz.mp4') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('source.mp3'), '-i', get_test_example_file('target-240p.mp4'), '-ar', '48000', get_test_example_file('target-240p-48khz.mp4') ])
	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('temp_frame_format', 'png')
	state_manager.init_item('output_audio_encoder', 'aac')
>>>>>>> origin/master


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
<<<<<<< HEAD
	facefusion.globals.trim_frame_start = None
	facefusion.globals.trim_frame_end = None
	facefusion.globals.temp_frame_format = 'jpg'


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

		assert extract_frames(target_path, '452x240', 30.0) is True
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

		assert extract_frames(target_path, '452x240', 30.0) is True
		assert len(glob.glob1(temp_directory_path, '*.jpg')) == frame_total

		clear_temp(target_path)


def test_extract_frames_with_trim_start_and_trim_end() -> None:
	facefusion.globals.trim_frame_start = 124
	facefusion.globals.trim_frame_end = 224
	data_provider =\
	[
		('.assets/examples/target-240p-25fps.mp4', 120),
		('.assets/examples/target-240p-30fps.mp4', 100),
		('.assets/examples/target-240p-60fps.mp4', 50)
	]

	for target_path, frame_total in data_provider:
		temp_directory_path = get_temp_directory_path(target_path)
		create_temp(target_path)

		assert extract_frames(target_path, '452x240', 30.0) is True
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

		assert extract_frames(target_path, '426x240', 30.0) is True
		assert len(glob.glob1(temp_directory_path, '*.jpg')) == frame_total

		clear_temp(target_path)


def test_read_audio_buffer() -> None:
	assert isinstance(read_audio_buffer('.assets/examples/source.mp3', 1, 1), bytes)
	assert isinstance(read_audio_buffer('.assets/examples/source.wav', 1, 1), bytes)
	assert read_audio_buffer('.assets/examples/invalid.mp3', 1, 1) is None
=======
	prepare_test_output_directory()


def test_extract_frames() -> None:
	extract_set =\
	[
		(get_test_example_file('target-240p-25fps.mp4'), 0, 270, 324),
		(get_test_example_file('target-240p-25fps.mp4'), 224, 270, 55),
		(get_test_example_file('target-240p-25fps.mp4'), 124, 224, 120),
		(get_test_example_file('target-240p-25fps.mp4'), 0, 100, 120),
		(get_test_example_file('target-240p-30fps.mp4'), 0, 324, 324),
		(get_test_example_file('target-240p-30fps.mp4'), 224, 324, 100),
		(get_test_example_file('target-240p-30fps.mp4'), 124, 224, 100),
		(get_test_example_file('target-240p-30fps.mp4'), 0, 100, 100),
		(get_test_example_file('target-240p-60fps.mp4'), 0, 648, 324),
		(get_test_example_file('target-240p-60fps.mp4'), 224, 648, 212),
		(get_test_example_file('target-240p-60fps.mp4'), 124, 224, 50),
		(get_test_example_file('target-240p-60fps.mp4'), 0, 100, 50)
	]

	for target_path, trim_frame_start, trim_frame_end, frame_total in extract_set:
		create_temp_directory(target_path)

		assert extract_frames(target_path, '452x240', 30.0, trim_frame_start, trim_frame_end) is True
		assert len(get_temp_frame_paths(target_path)) == frame_total

		clear_temp_directory(target_path)


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


def test_restore_audio() -> None:
	target_paths =\
	[
		get_test_example_file('target-240p-16khz.mp4'),
		get_test_example_file('target-240p-48khz.mp4')
	]
	output_path = get_test_output_file('test-restore-audio.mp4')

	for target_path in target_paths:
		create_temp_directory(target_path)
		copy_file(target_path, get_temp_file_path(target_path))

		assert restore_audio(target_path, output_path, 30, 0, 270) is True

		clear_temp_directory(target_path)


def test_replace_audio() -> None:
	target_path = get_test_example_file('target-240p.mp4')
	output_path = get_test_output_file('test-replace-audio.mp4')

	create_temp_directory(target_path)
	copy_file(target_path, get_temp_file_path(target_path))

	assert replace_audio(target_path, get_test_example_file('source.mp3'), output_path) is True
	assert replace_audio(target_path, get_test_example_file('source.wav'), output_path) is True

	clear_temp_directory(target_path)
>>>>>>> origin/master
