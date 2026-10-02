import os
import tempfile

import numpy
import pytest

from facefusion import ffmpeg, ffmpeg_builder, process_manager, state_manager, video_manager
from facefusion.audio import create_empty_audio_frame, get_audio_frame
from facefusion.download import conditional_download
from facefusion.filesystem import is_directory
from facefusion.temp_helper import get_temp_directory_path
from facefusion.vision import read_image, read_video_frame, write_image
from facefusion.workflows.core import clear, conditional_get_reference_vision_frame, conditional_get_source_audio_frame, conditional_get_source_voice_frame, conditional_get_target_vision_frames, detect_workflow_mode, is_process_stopping, process_frames, process_temp_frame, process_temp_vision_frame, setup
from .assert_helper import get_test_example_file, get_test_examples_directory, get_test_output_path, prepare_test_output_directory


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

	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('temp_frame_format', 'png')
	state_manager.init_item('reference_frame_index', 10)
	state_manager.init_item('trim_frame_start', None)
	state_manager.init_item('trim_frame_end', None)
	state_manager.init_item('output_video_fps', 25)
	state_manager.init_item('output_audio_fps', 25)
	state_manager.init_item('target_frame_amount', 1)
	state_manager.init_item('execution_thread_count', 2)
	state_manager.init_item('processors', [])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	prepare_test_output_directory()


def test_detect_workflow_mode() -> None:
	state_manager.init_item('source_paths', [ get_test_example_file('source.jpg') ])
	state_manager.init_item('target_path', get_test_example_file('target-240p.mp4'))
	state_manager.init_item('output_path', 'output.mp4')

	assert detect_workflow_mode() == 'image-to-video'

	state_manager.init_item('output_path', 'output')

	assert detect_workflow_mode() == 'image-to-video:frames'

	state_manager.init_item('source_paths', [ get_test_example_file('source.mp3') ])
	state_manager.init_item('target_path', get_test_example_file('source.jpg'))
	state_manager.init_item('output_path', 'output.jpg')

	assert detect_workflow_mode() == 'audio-to-image:video'

	state_manager.init_item('output_path', 'output')

	assert detect_workflow_mode() == 'audio-to-image:frames'

	state_manager.init_item('source_paths', [ get_test_example_file('source.jpg') ])
	state_manager.init_item('target_path', get_test_example_file('source.jpg'))

	assert detect_workflow_mode() == 'image-to-image'


def test_is_process_stopping() -> None:
	process_manager.start()

	assert is_process_stopping() is False
	assert process_manager.is_processing() is True

	process_manager.stop()

	assert is_process_stopping() is True
	assert process_manager.is_pending() is True

	process_manager.end()

	assert is_process_stopping() is True


def test_setup() -> None:
	state_manager.set_item('output_path', get_test_output_path('test-setup.mp4'))
	clear()

	assert setup() == 0
	assert get_temp_directory_path(state_manager.get_temp_path(), get_test_output_path('test-setup.mp4')) == os.path.join(state_manager.get_temp_path(), 'facefusion', 'test-setup')
	assert is_directory(get_temp_directory_path(state_manager.get_temp_path(), get_test_output_path('test-setup.mp4'))) is True

	clear()


def test_clear() -> None:
	state_manager.set_item('output_path', get_test_output_path('test-clear.mp4'))
	setup()

	assert clear() == 0
	assert is_directory(get_temp_directory_path(state_manager.get_temp_path(), get_test_output_path('test-clear.mp4'))) is False
	assert clear() == 0


def test_conditional_get_source_audio_frame() -> None:
	state_manager.set_item('source_paths', [ get_test_example_file('source.jpg'), get_test_example_file('source.mp3') ])
	state_manager.set_item('workflow_mode', 'image-to-image')
	state_manager.set_item('target_path', get_test_example_file('target-240p.jpg'))

	assert numpy.array_equal(conditional_get_source_audio_frame(10), create_empty_audio_frame()) is True

	state_manager.set_item('workflow_mode', 'audio-to-image:video')
	state_manager.set_item('output_audio_fps', 10)

	assert numpy.array_equal(conditional_get_source_audio_frame(10), get_audio_frame(get_test_example_file('source.mp3'), 10, 10)) is True

	state_manager.set_item('workflow_mode', 'audio-to-image:frames')

	assert numpy.array_equal(conditional_get_source_audio_frame(10), get_audio_frame(get_test_example_file('source.mp3'), 10, 10)) is True

	state_manager.set_item('workflow_mode', 'image-to-video')
	state_manager.set_item('target_path', get_test_example_file('target-240p.mp4'))

	assert numpy.array_equal(conditional_get_source_audio_frame(10), get_audio_frame(get_test_example_file('source.mp3'), 25, 10)) is True

	state_manager.set_item('trim_frame_start', 5)

	assert numpy.array_equal(conditional_get_source_audio_frame(10), get_audio_frame(get_test_example_file('source.mp3'), 25, 5)) is True
	assert numpy.array_equal(conditional_get_source_audio_frame(10), get_audio_frame(get_test_example_file('source.mp3'), 25, 10)) is False

	state_manager.set_item('output_video_fps', 10)

	assert numpy.array_equal(conditional_get_source_audio_frame(10), get_audio_frame(get_test_example_file('source.mp3'), 10, 5)) is True
	assert numpy.array_equal(conditional_get_source_audio_frame(10000), create_empty_audio_frame()) is True

	state_manager.set_item('source_paths', [ get_test_example_file('source.jpg') ])

	assert numpy.array_equal(conditional_get_source_audio_frame(10), create_empty_audio_frame()) is True

	state_manager.set_item('output_video_fps', 25)
	state_manager.set_item('output_audio_fps', 25)
	state_manager.clear_item('trim_frame_start')


@pytest.mark.xfail(strict = True, raises = AssertionError, reason = 'TESTING_AND_FIXING.md #7')
def test_conditional_get_source_audio_frame_with_frames_mode() -> None:
	state_manager.set_item('source_paths', [ get_test_example_file('source.jpg'), get_test_example_file('source.mp3') ])
	state_manager.set_item('workflow_mode', 'image-to-video:frames')
	state_manager.set_item('target_path', get_test_example_file('target-240p.mp4'))
	source_audio_frame = conditional_get_source_audio_frame(10)
	state_manager.set_item('source_paths', [ get_test_example_file('source.jpg') ])
	state_manager.set_item('workflow_mode', 'image-to-video')

	assert numpy.array_equal(source_audio_frame, get_audio_frame(get_test_example_file('source.mp3'), 25, 10)) is True


def test_conditional_get_source_voice_frame() -> None:
	state_manager.set_item('source_paths', [ get_test_example_file('source.jpg') ])
	state_manager.set_item('workflow_mode', 'image-to-image')
	state_manager.set_item('target_path', get_test_example_file('target-240p.jpg'))

	assert numpy.array_equal(conditional_get_source_voice_frame(10), create_empty_audio_frame()) is True

	state_manager.set_item('workflow_mode', 'image-to-video')
	state_manager.set_item('target_path', get_test_example_file('target-240p.mp4'))

	assert numpy.array_equal(conditional_get_source_voice_frame(10), create_empty_audio_frame()) is True

	state_manager.set_item('workflow_mode', 'audio-to-image:video')

	assert numpy.array_equal(conditional_get_source_voice_frame(10), create_empty_audio_frame()) is True


def test_conditional_get_reference_vision_frame() -> None:
	state_manager.set_item('workflow_mode', 'image-to-image')
	state_manager.set_item('target_path', get_test_example_file('target-240p.jpg'))

	assert numpy.array_equal(conditional_get_reference_vision_frame(), read_image(get_test_example_file('target-240p.jpg'))) is True

	state_manager.set_item('workflow_mode', 'image-to-video')
	state_manager.set_item('target_path', get_test_example_file('target-240p.mp4'))

	assert numpy.array_equal(conditional_get_reference_vision_frame(), read_video_frame(get_test_example_file('target-240p.mp4'), 10)) is True
	assert numpy.array_equal(conditional_get_reference_vision_frame(), read_video_frame(get_test_example_file('target-240p.mp4'), 0)) is False

	state_manager.set_item('workflow_mode', 'image-to-video:frames')

	assert numpy.array_equal(conditional_get_reference_vision_frame(), read_video_frame(get_test_example_file('target-240p.mp4'), 10)) is True


def test_conditional_get_target_vision_frames() -> None:
	state_manager.set_item('workflow_mode', 'image-to-image')
	state_manager.set_item('target_path', get_test_example_file('target-240p.jpg'))
	target_vision_frames = conditional_get_target_vision_frames(10)

	assert len(target_vision_frames) == 1
	assert numpy.array_equal(target_vision_frames[0], read_image(get_test_example_file('target-240p.jpg'))) is True

	state_manager.set_item('workflow_mode', 'image-to-video')
	state_manager.set_item('target_path', get_test_example_file('target-240p.mp4'))
	target_vision_frames = conditional_get_target_vision_frames(10)

	assert len(target_vision_frames) == 3
	assert numpy.array_equal(target_vision_frames[0], read_video_frame(get_test_example_file('target-240p.mp4'), 9)) is True
	assert numpy.array_equal(target_vision_frames[1], read_video_frame(get_test_example_file('target-240p.mp4'), 10)) is True
	assert numpy.array_equal(target_vision_frames[2], read_video_frame(get_test_example_file('target-240p.mp4'), 11)) is True

	state_manager.set_item('workflow_mode', 'image-to-video:frames')
	state_manager.set_item('trim_frame_start', 5)
	state_manager.set_item('output_video_fps', 10)
	state_manager.set_item('target_frame_amount', 0)
	target_vision_frames = conditional_get_target_vision_frames(6)

	assert len(target_vision_frames) == 1
	assert numpy.array_equal(target_vision_frames[0], read_video_frame(get_test_example_file('target-240p.mp4'), 8)) is True

	state_manager.set_item('target_frame_amount', 1)
	state_manager.set_item('output_video_fps', 25)
	state_manager.clear_item('trim_frame_start')


def test_process_temp_frame() -> None:
	state_manager.set_item('source_paths', [ get_test_example_file('source.jpg') ])
	state_manager.set_item('workflow_mode', 'image-to-image')
	state_manager.set_item('target_path', get_test_example_file('target-240p.jpg'))
	temp_vision_frame = read_image(get_test_example_file('target-240p.jpg'))
	temp_vision_mask = numpy.full(temp_vision_frame.shape[:2], 255, dtype = numpy.uint8)
	temp_vision_mask[:10, :10] = 0
	write_image(get_test_output_path('test-process-temp-frame.png'), numpy.dstack((temp_vision_frame, temp_vision_mask)))
	os.utime(get_test_output_path('test-process-temp-frame.png'), (0, 0))

	assert process_temp_frame(get_test_output_path('test-process-temp-frame.png'), 0) is True
	assert os.path.getmtime(get_test_output_path('test-process-temp-frame.png')) > 0
	assert numpy.array_equal(read_image(get_test_output_path('test-process-temp-frame.png'), 'rgba')[:, :, 3], temp_vision_mask) is True
	assert numpy.array_equal(read_image(get_test_output_path('test-process-temp-frame.png'), 'rgba')[:, :, :3], temp_vision_frame) is True


def test_process_temp_vision_frame() -> None:
	state_manager.set_item('source_paths', [ get_test_example_file('source.jpg') ])
	state_manager.set_item('workflow_mode', 'image-to-image')
	state_manager.set_item('target_path', get_test_example_file('target-240p.jpg'))
	target_vision_frames = [ read_image(get_test_example_file('target-240p.jpg')) ]
	temp_vision_frame = read_image(get_test_example_file('target-240p.jpg'))

	assert numpy.array_equal(process_temp_vision_frame(target_vision_frames, temp_vision_frame, 0), temp_vision_frame) is True

	temp_vision_mask = numpy.full(temp_vision_frame.shape[:2], 255, dtype = numpy.uint8)
	temp_vision_mask[:10, :10] = 0
	temp_vision_frame = numpy.dstack((temp_vision_frame, temp_vision_mask))

	assert process_temp_vision_frame(target_vision_frames, temp_vision_frame, 0).shape[2] == 4
	assert numpy.array_equal(process_temp_vision_frame(target_vision_frames, temp_vision_frame, 0)[:, :, 3], temp_vision_mask) is True


def test_process_frames() -> None:
	state_manager.set_item('source_paths', [ get_test_example_file('source.jpg') ])
	state_manager.set_item('workflow_mode', 'image-to-image')
	state_manager.set_item('target_path', get_test_example_file('target-240p.jpg'))
	state_manager.set_item('output_path', get_test_output_path('test-process-frames.mp4'))
	clear()
	process_manager.start()

	assert process_frames() == 1

	setup()
	temp_directory_path = get_temp_directory_path(state_manager.get_temp_path(), get_test_output_path('test-process-frames.mp4'))
	write_image(os.path.join(temp_directory_path, '00000000.png'), read_image(get_test_example_file('target-240p.jpg')))
	write_image(os.path.join(temp_directory_path, '00000001.png'), read_image(get_test_example_file('target-240p.jpg')))

	assert process_frames() == 0
	assert numpy.array_equal(read_image(os.path.join(temp_directory_path, '00000001.png')), read_image(get_test_example_file('target-240p.jpg'))) is True

	process_manager.end()

	assert process_frames() == 4

	clear()
