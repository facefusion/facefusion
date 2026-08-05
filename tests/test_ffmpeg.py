import os
import tempfile

import pytest

import facefusion.ffmpeg
from facefusion import ffmpeg, ffmpeg_builder, process_manager, state_manager
from facefusion.download import conditional_download
from facefusion.ffmpeg import concat_video, extract_frames, fix_audio_encoder, fix_video_encoder, merge_video, read_audio_buffer, replace_audio, restore_audio, sanitize_audio, sanitize_image, sanitize_video, spawn_frames
from facefusion.ffprobe import probe_audio_entries, probe_video_entries
from facefusion.filesystem import copy_file, is_image
from facefusion.temp_helper import clear_temp_directory, create_temp_directory, get_temp_file_path, resolve_temp_frame_paths
from facefusion.types import EncoderSet
from .assert_helper import get_test_example_file, get_test_examples_directory, get_test_output_path, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	process_manager.start()
	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('temp_frame_format', 'png')
	state_manager.init_item('output_audio_encoder', 'aac')
	state_manager.init_item('output_audio_quality', 100)
	state_manager.init_item('output_audio_volume', 100)
	state_manager.init_item('output_video_encoder', 'libx264')
	state_manager.init_item('output_video_quality', 100)
	state_manager.init_item('output_video_preset', 'ultrafast')

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])

	for video_fps in [ 25, 30, 60 ]:
		ffmpeg.run_ffmpeg(
			ffmpeg_builder.chain(
				ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
				ffmpeg_builder.set_video_fps(video_fps),
				ffmpeg_builder.set_output(get_test_example_file('target-240p-' + str(video_fps) + 'fps.mp4'))
			)
		)

	for output_video_format in [ 'avi', 'm4v', 'mkv', 'mov', 'mp4', 'webm', 'wmv' ]:
		ffmpeg.run_ffmpeg(
			ffmpeg_builder.chain(
				ffmpeg_builder.set_input(get_test_example_file('source.mp3')),
				ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
				ffmpeg_builder.set_audio_sample_rate(16000),
				ffmpeg_builder.set_output(get_test_example_file('target-240p-16khz.' + output_video_format))
			)
		)

	ffmpeg.run_ffmpeg(
		ffmpeg_builder.chain(
			ffmpeg_builder.set_input(get_test_example_file('source.mp3')),
			ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
			ffmpeg_builder.set_audio_sample_rate(48000),
			ffmpeg_builder.set_output(get_test_example_file('target-240p-48khz.mp4'))
		)
	)
	ffmpeg.run_ffmpeg(
		ffmpeg_builder.chain(
			ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
			ffmpeg_builder.set_video_encoder('libx265'),
			[
				'-an'
			],
			ffmpeg_builder.set_faststart('mp4'),
			ffmpeg_builder.set_output(get_test_example_file('target-240p-h265.mp4'))
		)
	)


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	prepare_test_output_directory()


def get_available_encoder_set() -> EncoderSet:
	if os.getenv('CI'):
		return\
		{
			'audio': [ 'aac' ],
			'image': [ 'png' ],
			'video': [ 'libx264' ]
		}
	return facefusion.ffmpeg.get_available_encoder_set()


def test_get_available_encoder_set() -> None:
	available_encoder_set = get_available_encoder_set()

	assert 'aac' in available_encoder_set.get('audio')
	assert 'png' in available_encoder_set.get('image')
	assert 'libx264' in available_encoder_set.get('video')


def test_extract_frames() -> None:
	test_set =\
	[
		(get_test_example_file('target-240p-25fps.mp4'), get_test_example_file('test-extract-frames-0-270.mp4'), 0, 270, 324),
		(get_test_example_file('target-240p-25fps.mp4'), get_test_example_file('test-extract-frames-224-270.mp4'), 224, 270, 55),
		(get_test_example_file('target-240p-25fps.mp4'), get_test_example_file('test-extract-frames-124-224.mp4'), 124, 224, 120),
		(get_test_example_file('target-240p-25fps.mp4'), get_test_example_file('test-extract-frames-0-100.mp4'), 0, 100, 120),
		(get_test_example_file('target-240p-30fps.mp4'), get_test_example_file('test-extract-frames-0-324.mp4'), 0, 324, 324),
		(get_test_example_file('target-240p-30fps.mp4'), get_test_example_file('test-extract-frames-224-324.mp4'), 224, 324, 100),
		(get_test_example_file('target-240p-30fps.mp4'), get_test_example_file('test-extract-frames-124-224.mp4'), 124, 224, 100),
		(get_test_example_file('target-240p-30fps.mp4'), get_test_example_file('test-extract-frames-0-100.mp4'), 0, 100, 100),
		(get_test_example_file('target-240p-60fps.mp4'), get_test_example_file('test-extract-frames-0-648.mp4'), 0, 648, 324),
		(get_test_example_file('target-240p-60fps.mp4'), get_test_example_file('test-extract-frames-224-648.mp4'), 224, 648, 212),
		(get_test_example_file('target-240p-60fps.mp4'), get_test_example_file('test-extract-frames-124-224.mp4'), 124, 224, 50),
		(get_test_example_file('target-240p-60fps.mp4'), get_test_example_file('test-extract-frames-0-100.mp4'), 0, 100, 50)
	]

	for target_path, output_path, trim_frame_start, trim_frame_end, frame_total in test_set:
		create_temp_directory(state_manager.get_temp_path(), output_path)

		assert extract_frames(target_path, output_path, (452, 240), 30.0, trim_frame_start, trim_frame_end) is True
		assert len(resolve_temp_frame_paths(state_manager.get_temp_path(), output_path, state_manager.get_item('temp_frame_format'))) == frame_total

		clear_temp_directory(state_manager.get_temp_path(), output_path)


def test_spawn_frames() -> None:
	test_set =\
	[
		(get_test_example_file('source.jpg'), get_test_example_file('test-spawn-frames-0-100.mp4'), 0, 100, 30.0, 100),
		(get_test_example_file('source.jpg'), get_test_example_file('test-spawn-frames-0-150.mp4'), 0, 150, 30.0, 150),
		(get_test_example_file('source.jpg'), get_test_example_file('test-spawn-frames-50-100.mp4'), 50, 100, 25.0, 50),
		(get_test_example_file('source.jpg'), get_test_example_file('test-spawn-frames-0-300.mp4'), 0, 300, 60.0, 300),
		(get_test_example_file('source.jpg'), get_test_example_file('test-spawn-frames-100-200.mp4'), 100, 200, 30.0, 100)
	]

	for target_path, output_path, trim_frame_start, trim_frame_end, temp_video_fps, frame_total in test_set:
		create_temp_directory(state_manager.get_temp_path(), output_path)

		assert spawn_frames(target_path, output_path, (452, 240), temp_video_fps, trim_frame_start, trim_frame_end) is True
		assert len(resolve_temp_frame_paths(state_manager.get_temp_path(), output_path, state_manager.get_item('temp_frame_format'))) == frame_total

		clear_temp_directory(state_manager.get_temp_path(), output_path)


def test_merge_video() -> None:
	test_set =\
	[
		(get_test_example_file('target-240p-16khz.avi'), get_test_output_path('test-merge-video-240p-16khz.avi')),
		(get_test_example_file('target-240p-16khz.m4v'), get_test_output_path('test-merge-video-240p-16khz.m4v')),
		(get_test_example_file('target-240p-16khz.mkv'), get_test_output_path('test-merge-video-240p-16khz.mkv')),
		(get_test_example_file('target-240p-16khz.mp4'), get_test_output_path('test-merge-video-240p-16khz.mp4')),
		(get_test_example_file('target-240p-16khz.mov'), get_test_output_path('test-merge-video-240p-16khz.mov')),
		(get_test_example_file('target-240p-16khz.webm'), get_test_output_path('test-merge-video-240p-16khz.webm')),
		(get_test_example_file('target-240p-16khz.wmv'), get_test_output_path('test-merge-video-240p-16khz.wmv'))
	]
	output_video_encoders = get_available_encoder_set().get('video')

	for target_path, output_path in test_set:
		for output_video_encoder in output_video_encoders:
			state_manager.init_item('output_path', target_path)
			state_manager.init_item('output_video_fps', 25.0)
			state_manager.init_item('output_video_encoder', output_video_encoder)
			create_temp_directory(state_manager.get_temp_path(), output_path)
			extract_frames(target_path, output_path, (452, 240), 25.0, 0, 1)

			assert merge_video(target_path, output_path, 25.0, 25.0, (452, 240), 0, 1) is True

			clear_temp_directory(state_manager.get_temp_path(), output_path)

	state_manager.init_item('output_video_encoder', 'libx264')


def test_concat_video() -> None:
	output_path = get_test_output_path('test-concat-video.mp4')
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
		(get_test_example_file('target-240p-16khz.avi'), get_test_output_path('target-240p-16khz.avi')),
		(get_test_example_file('target-240p-16khz.m4v'), get_test_output_path('target-240p-16khz.m4v')),
		(get_test_example_file('target-240p-16khz.mkv'), get_test_output_path('target-240p-16khz.mkv')),
		(get_test_example_file('target-240p-16khz.mov'), get_test_output_path('target-240p-16khz.mov')),
		(get_test_example_file('target-240p-16khz.mp4'), get_test_output_path('target-240p-16khz.mp4')),
		(get_test_example_file('target-240p-48khz.mp4'), get_test_output_path('target-240p-48khz.mp4')),
		(get_test_example_file('target-240p-16khz.webm'), get_test_output_path('target-240p-16khz.webm')),
		(get_test_example_file('target-240p-16khz.wmv'), get_test_output_path('target-240p-16khz.wmv'))
	]
	output_audio_encoders = get_available_encoder_set().get('audio')

	for target_path, output_path in test_set:
		create_temp_directory(state_manager.get_temp_path(), output_path)

		for output_audio_encoder in output_audio_encoders:
			state_manager.init_item('output_audio_encoder', output_audio_encoder)
			copy_file(target_path, get_temp_file_path(state_manager.get_temp_path(), output_path))

			assert restore_audio(target_path, output_path, 0, 270) is True

		clear_temp_directory(state_manager.get_temp_path(), output_path)

	state_manager.init_item('output_audio_encoder', 'aac')


def test_replace_audio() -> None:
	test_set =\
	[
		(get_test_example_file('target-240p-16khz.avi'), get_test_output_path('target-240p-16khz.avi')),
		(get_test_example_file('target-240p-16khz.m4v'), get_test_output_path('target-240p-16khz.m4v')),
		(get_test_example_file('target-240p-16khz.mkv'), get_test_output_path('target-240p-16khz.mkv')),
		(get_test_example_file('target-240p-16khz.mov'), get_test_output_path('target-240p-16khz.mov')),
		(get_test_example_file('target-240p-16khz.mp4'), get_test_output_path('target-240p-16khz.mp4')),
		(get_test_example_file('target-240p-48khz.mp4'), get_test_output_path('target-240p-48khz.mp4')),
		(get_test_example_file('target-240p-16khz.webm'), get_test_output_path('target-240p-16khz.webm'))
	]
	output_audio_encoders = get_available_encoder_set().get('audio')

	for target_path, output_path in test_set:
		create_temp_directory(state_manager.get_temp_path(), output_path)

		for output_audio_encoder in output_audio_encoders:
			state_manager.init_item('output_audio_encoder', output_audio_encoder)
			copy_file(target_path, get_temp_file_path(state_manager.get_temp_path(), output_path))

			assert replace_audio(get_test_example_file('source.mp3'), output_path) is True
			assert replace_audio(get_test_example_file('source.wav'), output_path) is True

		clear_temp_directory(state_manager.get_temp_path(), output_path)

	state_manager.init_item('output_audio_encoder', 'aac')


def test_sanitize_audio() -> None:
	file_path = get_test_example_file('source.wav')
	file_content = open(file_path, 'rb').read()
	output_paths =\
	[
		get_test_output_path('test-sanitize-audio-strict.mp3'),
		get_test_output_path('test-sanitize-audio-moderate.wav')
	]

	assert sanitize_audio(file_content, output_paths[0], 'strict') is True
	assert probe_audio_entries(output_paths[0], [ 'codec_name' ]).get('codec_name') == 'mp3'

	assert sanitize_audio(file_content, output_paths[1], 'moderate') is True
	assert probe_audio_entries(output_paths[1], [ 'codec_name' ]).get('codec_name') == 'pcm_s16le'


def test_sanitize_image() -> None:
	file_path = get_test_example_file('source.jpg')
	file_content = open(file_path, 'rb').read()
	output_path = get_test_output_path('test-sanitize-image.jpg')

	assert sanitize_image(file_content, output_path) is True
	assert is_image(output_path) is True


def test_sanitize_video() -> None:
	file_path = get_test_example_file('target-240p-h265.mp4')
	file_content = open(file_path, 'rb').read()
	output_paths =\
	[
		get_test_output_path('test-sanitize-video-strict.mp4'),
		get_test_output_path('test-sanitize-video-moderate.mp4')
	]

	assert sanitize_video(file_content, output_paths[0], 'strict') is True
	assert probe_video_entries(output_paths[0], [ 'codec_name' ]).get('codec_name') == 'h264'

	assert sanitize_video(file_content, output_paths[1], 'moderate') is True
	assert probe_video_entries(output_paths[1], [ 'codec_name' ]).get('codec_name') == 'hevc'


def test_fix_audio_encoder() -> None:
	assert fix_audio_encoder('avi', 'libopus') == 'aac'
	assert fix_audio_encoder('m4v', 'libopus') == 'aac'
	assert fix_audio_encoder('mpeg', 'libopus') == 'aac'
	assert fix_audio_encoder('wmv', 'libopus') == 'aac'
	assert fix_audio_encoder('mov', 'flac') == 'aac'
	assert fix_audio_encoder('mov', 'libopus') == 'aac'
	assert fix_audio_encoder('mxf', 'libopus') == 'pcm_s16le'
	assert fix_audio_encoder('webm', 'aac') == 'libopus'
	assert fix_audio_encoder('mp4', 'aac') == 'aac'
	assert fix_audio_encoder('avi', 'aac') == 'aac'


def test_fix_video_encoder() -> None:
	assert fix_video_encoder('m4v', 'libx265') == 'libx264'
	assert fix_video_encoder('mpeg', 'libx265') == 'libx264'
	assert fix_video_encoder('mxf', 'libx265') == 'libx264'
	assert fix_video_encoder('wmv', 'libx265') == 'libx264'
	assert fix_video_encoder('mkv', 'rawvideo') == 'libx264'
	assert fix_video_encoder('mp4', 'rawvideo') == 'libx264'
	assert fix_video_encoder('mov', 'libvpx-vp9') == 'libx264'
	assert fix_video_encoder('webm', 'libx264') == 'libvpx-vp9'
	assert fix_video_encoder('mp4', 'libx265') == 'libx265'
	assert fix_video_encoder('avi', 'rawvideo') == 'rawvideo'


