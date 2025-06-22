import os
import subprocess
import tempfile

import pytest

import facefusion.ffmpeg
from facefusion import process_manager, state_manager
from facefusion.download import conditional_download
from facefusion.ffmpeg import concat_video, extract_frames, merge_video, read_audio_buffer, replace_audio, restore_audio
from facefusion.filesystem import copy_file
from facefusion.temp_helper import clear_temp_directory, create_temp_directory, get_temp_file_path, resolve_temp_frame_paths
from facefusion.types import EncoderSet
from .helper import get_test_example_file, get_test_examples_directory, get_test_output_file, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	process_manager.start()
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

	for output_video_format in [ 'avi', 'm4v', 'mkv', 'mov', 'mp4', 'webm' ]:
		subprocess.run([ 'ffmpeg', '-i', get_test_example_file('source.mp3'), '-i', get_test_example_file('target-240p.mp4'), '-ar', '16000', get_test_example_file('target-240p-16khz.' + output_video_format) ])

	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('source.mp3'), '-i', get_test_example_file('target-240p.mp4'), '-ar', '48000', get_test_example_file('target-240p-48khz.mp4') ])
	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('temp_frame_format', 'png')
	state_manager.init_item('output_audio_encoder', 'aac')
	state_manager.init_item('output_audio_quality', 100)
	state_manager.init_item('output_audio_volume', 100)
	state_manager.init_item('output_video_encoder', 'libx264')
	state_manager.init_item('output_video_quality', 100)
	state_manager.init_item('output_video_preset', 'ultrafast')


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	prepare_test_output_directory()


def get_available_encoder_set() -> EncoderSet:
	if os.getenv('CI'):
		return\
		{
			'audio': [ 'aac' ],
			'video': [ 'libx264' ]
		}
	return facefusion.ffmpeg.get_available_encoder_set()


def test_get_available_encoder_set() -> None:
	available_encoder_set = get_available_encoder_set()

	assert 'aac' in available_encoder_set.get('audio')
	assert 'libx264' in available_encoder_set.get('video')


def test_extract_frames() -> None:
	test_set =\
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

	for target_path, trim_frame_start, trim_frame_end, frame_total in test_set:
		create_temp_directory(target_path)

		assert extract_frames(target_path, '452x240', 30.0, trim_frame_start, trim_frame_end) is True
		assert len(resolve_temp_frame_paths(target_path)) == frame_total

		clear_temp_directory(target_path)


def test_merge_video() -> None:
	target_paths =\
	[
		get_test_example_file('target-240p-16khz.avi'),
		get_test_example_file('target-240p-16khz.m4v'),
		get_test_example_file('target-240p-16khz.mkv'),
		get_test_example_file('target-240p-16khz.mp4'),
		get_test_example_file('target-240p-16khz.mov'),
		get_test_example_file('target-240p-16khz.webm')
	]
	output_video_encoders = get_available_encoder_set().get('video')

	for target_path in target_paths:
		for output_video_encoder in output_video_encoders:
			state_manager.init_item('output_video_encoder', output_video_encoder)
			create_temp_directory(target_path)
			extract_frames(target_path, '452x240', 25.0, 0, 1)

			assert merge_video(target_path, 25.0, '452x240', 25.0, 0, 1) is True

		clear_temp_directory(target_path)

	state_manager.init_item('output_video_encoder', 'libx264')


def test_concat_video() -> None:
	output_path = get_test_output_file('test-concat-video.mp4')
	temp_output_paths =\
	[
		get_test_example_file('target-240p-16khz.mp4'),
		get_test_example_file('target-240p-16khz.mp4')
	]

	assert concat_video(output_path, temp_output_paths) is True


def test_read_audio_buffer() -> None:
	assert isinstance(read_audio_buffer(get_test_example_file('source.mp3'), 1, 16, 1), bytes)
	assert isinstance(read_audio_buffer(get_test_example_file('source.wav'), 1, 16, 1), bytes)
	assert read_audio_buffer(get_test_example_file('invalid.mp3'), 1, 16, 1) is None


def test_restore_audio() -> None:
	test_set =\
	[
		(get_test_example_file('target-240p-16khz.avi'), get_test_output_file('target-240p-16khz.avi')),
		(get_test_example_file('target-240p-16khz.m4v'), get_test_output_file('target-240p-16khz.m4v')),
		(get_test_example_file('target-240p-16khz.mkv'), get_test_output_file('target-240p-16khz.mkv')),
		(get_test_example_file('target-240p-16khz.mov'), get_test_output_file('target-240p-16khz.mov')),
		(get_test_example_file('target-240p-16khz.mp4'), get_test_output_file('target-240p-16khz.mp4')),
		(get_test_example_file('target-240p-48khz.mp4'), get_test_output_file('target-240p-48khz.mp4')),
		(get_test_example_file('target-240p-16khz.webm'), get_test_output_file('target-240p-16khz.webm'))
	]
	output_audio_encoders = get_available_encoder_set().get('audio')

	for target_path, output_path in test_set:
		create_temp_directory(target_path)

		for output_audio_encoder in output_audio_encoders:
			state_manager.init_item('output_audio_encoder', output_audio_encoder)
			copy_file(target_path, get_temp_file_path(target_path))

			assert restore_audio(target_path, output_path, 0, 270) is True

		clear_temp_directory(target_path)

	state_manager.init_item('output_audio_encoder', 'aac')


def test_replace_audio() -> None:
	test_set =\
	[
		(get_test_example_file('target-240p-16khz.avi'), get_test_output_file('target-240p-16khz.avi')),
		(get_test_example_file('target-240p-16khz.m4v'), get_test_output_file('target-240p-16khz.m4v')),
		(get_test_example_file('target-240p-16khz.mkv'), get_test_output_file('target-240p-16khz.mkv')),
		(get_test_example_file('target-240p-16khz.mov'), get_test_output_file('target-240p-16khz.mov')),
		(get_test_example_file('target-240p-16khz.mp4'), get_test_output_file('target-240p-16khz.mp4')),
		(get_test_example_file('target-240p-48khz.mp4'), get_test_output_file('target-240p-48khz.mp4')),
		(get_test_example_file('target-240p-16khz.webm'), get_test_output_file('target-240p-16khz.webm'))
	]
	output_audio_encoders = get_available_encoder_set().get('audio')

	for target_path, output_path in test_set:
		create_temp_directory(target_path)

		for output_audio_encoder in output_audio_encoders:
			state_manager.init_item('output_audio_encoder', output_audio_encoder)
			copy_file(target_path, get_temp_file_path(target_path))

			assert replace_audio(target_path, get_test_example_file('source.mp3'), output_path) is True
			assert replace_audio(target_path, get_test_example_file('source.wav'), output_path) is True

		clear_temp_directory(target_path)

	state_manager.init_item('output_audio_encoder', 'aac')
