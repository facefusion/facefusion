import tempfile
from time import time
from unittest.mock import patch

import cv2
import numpy
import pytest

from facefusion import ffmpeg, ffmpeg_builder, process_manager, state_manager, video_manager
from facefusion.download import conditional_download
from facefusion.ffprobe import extract_video_metadata, probe_audio_entries
from facefusion.filesystem import copy_file, is_file
from facefusion.temp_helper import clear_temp_directory, create_temp_directory, get_temp_file_path, resolve_temp_frame_paths
from facefusion.vision import detect_image_resolution, read_video_frame
from facefusion.workflows.to_video import analyse_video, conditional_get_output_fps, conditional_restrict_video_fps, conditional_scale_resolution, create_temp_frames, finalize_video, merge_frames, process_memory_frame, process_memory_frames, restore_audio
from .assert_helper import get_test_example_file, get_test_examples_directory, get_test_output_path, is_test_output_file, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()

	video_manager.init()

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])

	ffmpeg.run_ffmpeg(
		ffmpeg_builder.chain(
			ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
			[
				'-vframes',
				'1'
			],
			ffmpeg_builder.set_output(get_test_example_file('target-240p.jpg'))
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

	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('temp_frame_format', 'png')
	state_manager.init_item('trim_frame_start', None)
	state_manager.init_item('trim_frame_end', None)
	state_manager.init_item('output_audio_encoder', 'aac')
	state_manager.init_item('output_audio_quality', 100)
	state_manager.init_item('output_audio_volume', 100)
	state_manager.init_item('output_video_encoder', 'libx264')
	state_manager.init_item('output_video_quality', 100)
	state_manager.init_item('output_video_preset', 'ultrafast')
	state_manager.init_item('output_video_fps', 30)
	state_manager.init_item('output_audio_fps', 20)
	state_manager.init_item('output_video_scale', 2.0)
	state_manager.init_item('reference_frame_index', 0)
	state_manager.init_item('target_frame_amount', 1)
	state_manager.init_item('temp_pixel_format', 'bgr24')
	state_manager.init_item('execution_thread_count', 2)
	state_manager.init_item('processors', [])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	prepare_test_output_directory()


def test_analyse_video() -> None:
	state_manager.set_item('target_path', get_test_example_file('target-240p.mp4'))

	with patch('facefusion.content_analyser.analyse_video', return_value = True) as analyse_video_mock:
		assert analyse_video() == 3

	analyse_video_mock.assert_called_once_with(get_test_example_file('target-240p.mp4'), 0, 270)

	state_manager.set_item('trim_frame_start', 5)
	state_manager.set_item('trim_frame_end', 15)

	with patch('facefusion.content_analyser.analyse_video', return_value = False) as analyse_video_mock:
		assert analyse_video() == 0

	analyse_video_mock.assert_called_once_with(get_test_example_file('target-240p.mp4'), 5, 15)

	state_manager.clear_item('trim_frame_start')
	state_manager.clear_item('trim_frame_end')


def test_create_temp_frames() -> None:
	state_manager.set_item('workflow_mode', 'image-to-video')
	state_manager.set_item('target_path', get_test_example_file('target-240p.mp4'))
	state_manager.set_item('output_path', get_test_output_path('test-create-temp-frames.mp4'))
	state_manager.set_item('trim_frame_start', 5)
	state_manager.set_item('trim_frame_end', 15)
	state_manager.set_item('output_video_scale', 0.5)
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-create-temp-frames.mp4'))
	process_manager.start()

	assert create_temp_frames() == 1

	process_manager.stop()

	assert create_temp_frames() == 4
	assert process_manager.is_pending() is True

	process_manager.start()
	create_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-create-temp-frames.mp4'))

	assert create_temp_frames() == 0
	assert len(resolve_temp_frame_paths(state_manager.get_temp_path(), get_test_output_path('test-create-temp-frames.mp4'), 'png')) == 10
	assert detect_image_resolution(resolve_temp_frame_paths(state_manager.get_temp_path(), get_test_output_path('test-create-temp-frames.mp4'), 'png')[0]) == (212, 112)

	process_manager.end()
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-create-temp-frames.mp4'))
	state_manager.set_item('output_video_scale', 2.0)
	state_manager.clear_item('trim_frame_start')
	state_manager.clear_item('trim_frame_end')


def test_process_memory_frame() -> None:
	state_manager.set_item('workflow_mode', 'image-to-video')
	state_manager.set_item('source_paths', [ get_test_example_file('source.jpg') ])
	state_manager.set_item('target_path', get_test_example_file('target-240p.mp4'))
	state_manager.set_item('output_video_fps', 25)
	state_manager.set_item('temp_pixel_format', 'bgr24')
	target_vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'), 10)

	assert numpy.array_equal(process_memory_frame(10, (426, 226), (426, 226)), target_vision_frame) is True
	assert process_memory_frame(10, (426, 226), (852, 452)).shape == (452, 852, 3)
	assert numpy.array_equal(process_memory_frame(10, (212, 112), (426, 226)), cv2.resize(cv2.resize(target_vision_frame, (212, 112)), (426, 226))) is True

	state_manager.set_item('temp_pixel_format', 'bgra')

	assert process_memory_frame(10, (426, 226), (426, 226)).shape == (226, 426, 4)
	assert numpy.array_equal(process_memory_frame(10, (426, 226), (426, 226))[:, :, :3], target_vision_frame) is True
	assert numpy.array_equal(process_memory_frame(10, (426, 226), (426, 226))[:, :, 3], numpy.full((226, 426), 255)) is True

	state_manager.set_item('temp_pixel_format', 'bgr24')
	state_manager.set_item('output_video_fps', 30)


def test_process_memory_frames() -> None:
	state_manager.set_item('workflow_mode', 'image-to-video')
	state_manager.set_item('source_paths', [ get_test_example_file('source.jpg') ])
	state_manager.set_item('target_path', get_test_example_file('target-240p.mp4'))
	state_manager.set_item('output_path', get_test_output_path('test-process-memory-frames.mp4'))
	state_manager.set_item('trim_frame_start', 5)
	state_manager.set_item('trim_frame_end', 15)
	state_manager.set_item('output_video_fps', 25)
	state_manager.set_item('output_video_scale', 1.0)
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-process-memory-frames.mp4'))
	create_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-process-memory-frames.mp4'))
	process_manager.start()

	assert process_memory_frames() == 0
	assert extract_video_metadata(get_temp_file_path(state_manager.get_temp_path(), get_test_output_path('test-process-memory-frames.mp4'))).get('frame_total') == 10
	assert extract_video_metadata(get_temp_file_path(state_manager.get_temp_path(), get_test_output_path('test-process-memory-frames.mp4'))).get('resolution') == (426, 226)

	state_manager.set_item('trim_frame_start', 15)

	assert process_memory_frames() == 1

	state_manager.set_item('trim_frame_start', 5)
	process_manager.stop()

	assert process_memory_frames() == 4
	assert process_manager.is_pending() is True

	process_manager.end()
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-process-memory-frames.mp4'))
	state_manager.set_item('output_video_fps', 30)
	state_manager.set_item('output_video_scale', 2.0)
	state_manager.clear_item('trim_frame_start')
	state_manager.clear_item('trim_frame_end')


def test_merge_frames() -> None:
	state_manager.set_item('workflow_mode', 'image-to-video')
	state_manager.set_item('target_path', get_test_example_file('target-240p.mp4'))
	state_manager.set_item('output_path', get_test_output_path('test-merge-frames.mp4'))
	state_manager.set_item('trim_frame_start', 5)
	state_manager.set_item('trim_frame_end', 15)
	state_manager.set_item('output_video_fps', 25)
	state_manager.set_item('output_video_scale', 1.0)
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-merge-frames.mp4'))
	create_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-merge-frames.mp4'))
	process_manager.start()

	assert merge_frames() == 1

	process_manager.stop()

	assert merge_frames() == 4
	assert process_manager.is_pending() is True

	process_manager.start()
	create_temp_frames()

	assert merge_frames() == 0
	assert extract_video_metadata(get_temp_file_path(state_manager.get_temp_path(), get_test_output_path('test-merge-frames.mp4'))).get('frame_total') == 10
	assert extract_video_metadata(get_temp_file_path(state_manager.get_temp_path(), get_test_output_path('test-merge-frames.mp4'))).get('resolution') == (426, 226)

	process_manager.end()
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-merge-frames.mp4'))
	state_manager.set_item('output_video_fps', 30)
	state_manager.set_item('output_video_scale', 2.0)
	state_manager.clear_item('trim_frame_start')
	state_manager.clear_item('trim_frame_end')


def test_restore_audio() -> None:
	state_manager.set_item('workflow_mode', 'image-to-video')
	state_manager.set_item('source_paths', [ get_test_example_file('source.jpg') ])
	state_manager.set_item('target_path', get_test_example_file('target-240p.mp4'))
	state_manager.set_item('output_path', get_test_output_path('test-restore-audio.mp4'))
	state_manager.set_item('output_audio_volume', 0)
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-restore-audio.mp4'))
	create_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-restore-audio.mp4'))
	copy_file(get_test_example_file('target-240p.mp4'), get_temp_file_path(state_manager.get_temp_path(), get_test_output_path('test-restore-audio.mp4')))
	process_manager.start()

	assert restore_audio() == 0
	assert is_test_output_file('test-restore-audio.mp4') is True
	assert is_file(get_temp_file_path(state_manager.get_temp_path(), get_test_output_path('test-restore-audio.mp4'))) is False

	state_manager.set_item('source_paths', [ get_test_example_file('source.jpg'), get_test_example_file('source.mp3') ])
	state_manager.set_item('output_path', get_test_output_path('test-restore-audio-replace.mp4'))
	state_manager.set_item('output_audio_volume', 100)
	create_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-restore-audio-replace.mp4'))
	copy_file(get_test_example_file('target-240p.mp4'), get_temp_file_path(state_manager.get_temp_path(), get_test_output_path('test-restore-audio-replace.mp4')))

	assert restore_audio() == 0
	assert is_test_output_file('test-restore-audio-replace.mp4') is True

	state_manager.set_item('output_path', get_test_output_path('test-restore-audio-replace-skip.mp4'))
	create_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-restore-audio-replace-skip.mp4'))

	assert restore_audio() == 0
	assert is_test_output_file('test-restore-audio-replace-skip.mp4') is False

	process_manager.stop()

	assert restore_audio() == 4
	assert process_manager.is_pending() is True

	state_manager.set_item('source_paths', [ get_test_example_file('source.jpg') ])
	state_manager.set_item('target_path', get_test_example_file('target-240p-48khz.mp4'))
	state_manager.set_item('output_path', get_test_output_path('test-restore-audio-restore.mp4'))
	state_manager.set_item('output_video_fps', 25)
	state_manager.set_item('output_video_scale', 0.5)
	create_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-restore-audio-restore.mp4'))
	copy_file(get_test_example_file('target-240p-48khz.mp4'), get_temp_file_path(state_manager.get_temp_path(), get_test_output_path('test-restore-audio-restore.mp4')))
	process_manager.start()
	create_temp_frames()

	assert restore_audio() == 0
	assert probe_audio_entries(get_test_output_path('test-restore-audio-restore.mp4'), [ 'duration' ]) == { 'duration': '3.797000' }

	state_manager.set_item('output_path', get_test_output_path('test-restore-audio-restore-skip.mp4'))
	state_manager.set_item('target_path', get_test_example_file('target-240p.mp4'))
	create_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-restore-audio-restore-skip.mp4'))
	copy_file(get_test_example_file('target-240p.mp4'), get_temp_file_path(state_manager.get_temp_path(), get_test_output_path('test-restore-audio-restore-skip.mp4')))

	assert restore_audio() == 0
	assert is_test_output_file('test-restore-audio-restore-skip.mp4') is True
	assert is_file(get_temp_file_path(state_manager.get_temp_path(), get_test_output_path('test-restore-audio-restore-skip.mp4'))) is False

	process_manager.stop()

	assert restore_audio() == 4
	assert process_manager.is_pending() is True

	process_manager.end()
	state_manager.set_item('output_video_fps', 30)
	state_manager.set_item('output_video_scale', 2.0)
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-restore-audio.mp4'))
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-restore-audio-replace.mp4'))
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-restore-audio-replace-skip.mp4'))
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-restore-audio-restore.mp4'))
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-restore-audio-restore-skip.mp4'))


def test_finalize_video() -> None:
	state_manager.set_item('output_path', get_test_example_file('target-240p.mp4'))

	assert finalize_video(time()) == 0

	state_manager.set_item('output_path', get_test_example_file('target-240p.jpg'))

	assert finalize_video(time()) == 1

	state_manager.set_item('output_path', 'invalid')

	assert finalize_video(time()) == 1


def test_conditional_restrict_video_fps() -> None:
	state_manager.set_item('workflow_mode', 'image-to-video')
	state_manager.set_item('target_path', get_test_example_file('target-240p.mp4'))

	assert conditional_restrict_video_fps() == 25.0

	state_manager.set_item('output_video_fps', 10)

	assert conditional_restrict_video_fps() == 10

	state_manager.set_item('workflow_mode', 'image-to-video:frames')

	assert conditional_restrict_video_fps() == 10

	state_manager.set_item('workflow_mode', 'audio-to-image:video')
	state_manager.set_item('target_path', get_test_example_file('source.jpg'))

	assert conditional_restrict_video_fps() == 20

	state_manager.set_item('output_video_fps', 30)


def test_conditional_get_output_fps() -> None:
	state_manager.set_item('workflow_mode', 'image-to-video')

	assert conditional_get_output_fps() == 30

	state_manager.set_item('workflow_mode', 'audio-to-image:video')

	assert conditional_get_output_fps() == 20

	state_manager.set_item('workflow_mode', 'audio-to-image:frames')

	assert conditional_get_output_fps() == 20


def test_conditional_scale_resolution() -> None:
	state_manager.set_item('workflow_mode', 'image-to-video')
	state_manager.set_item('target_path', get_test_example_file('target-240p.mp4'))

	assert conditional_scale_resolution() == (852, 452)

	state_manager.set_item('workflow_mode', 'audio-to-image:video')
	state_manager.set_item('target_path', get_test_example_file('source.jpg'))
	state_manager.set_item('output_video_scale', 0.5)

	assert conditional_scale_resolution() == (512, 512)

	state_manager.set_item('output_video_scale', 2.0)
