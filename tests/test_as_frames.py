import os
import tempfile
from time import time

import pytest

from facefusion import ffmpeg, ffmpeg_builder, process_manager, state_manager
from facefusion.download import conditional_download
from facefusion.filesystem import copy_file, create_directory, resolve_file_paths
from facefusion.temp_helper import clear_temp_directory, create_temp_directory, get_temp_directory_path, resolve_temp_frame_paths
from facefusion.vision import detect_image_resolution
from facefusion.workflows.as_frames import copy_temp_frames, create_temp_frames, finalize_frames
from .assert_helper import get_test_example_file, get_test_examples_directory, get_test_output_path, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()

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
	state_manager.init_item('output_audio_fps', 25)
	state_manager.init_item('output_image_scale', 1.0)
	state_manager.init_item('trim_frame_start', None)
	state_manager.init_item('trim_frame_end', None)


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	prepare_test_output_directory()


def test_create_temp_frames() -> None:
	state_manager.set_item('source_paths', [ get_test_example_file('source.jpg'), get_test_example_file('source.mp3') ])
	state_manager.set_item('target_path', get_test_example_file('target-240p.jpg'))
	state_manager.set_item('output_path', get_test_output_path('test-create-temp-frames'))
	state_manager.set_item('trim_frame_start', 5)
	state_manager.set_item('trim_frame_end', 15)
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-create-temp-frames'))
	process_manager.start()

	assert create_temp_frames() == 1

	process_manager.stop()

	assert create_temp_frames() == 4
	assert process_manager.is_pending() is True

	process_manager.start()
	create_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-create-temp-frames'))

	assert create_temp_frames() == 0
	assert len(resolve_temp_frame_paths(state_manager.get_temp_path(), get_test_output_path('test-create-temp-frames'), 'png')) == 10
	assert detect_image_resolution(resolve_temp_frame_paths(state_manager.get_temp_path(), get_test_output_path('test-create-temp-frames'), 'png')[0]) == (426, 226)

	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-create-temp-frames'))
	create_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-create-temp-frames'))
	state_manager.set_item('output_image_scale', 0.5)

	assert create_temp_frames() == 0
	assert detect_image_resolution(resolve_temp_frame_paths(state_manager.get_temp_path(), get_test_output_path('test-create-temp-frames'), 'png')[0]) == (212, 112)

	process_manager.end()
	state_manager.set_item('output_image_scale', 1.0)
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-create-temp-frames'))
	state_manager.clear_item('trim_frame_start')
	state_manager.clear_item('trim_frame_end')


def test_copy_temp_frames() -> None:
	state_manager.set_item('output_path', get_test_output_path('test-copy-temp-frames'))
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-copy-temp-frames'))
	create_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-copy-temp-frames'))
	temp_directory_path = get_temp_directory_path(state_manager.get_temp_path(), get_test_output_path('test-copy-temp-frames'))
	copy_file(get_test_example_file('target-240p.jpg'), os.path.join(temp_directory_path, '00000000.png'))
	copy_file(get_test_example_file('target-240p.jpg'), os.path.join(temp_directory_path, '00000001.png'))

	assert copy_temp_frames() == 0
	assert resolve_file_paths(get_test_output_path('test-copy-temp-frames')) == [ get_test_output_path(os.path.join('test-copy-temp-frames', '00000000.png')), get_test_output_path(os.path.join('test-copy-temp-frames', '00000001.png')) ]

	state_manager.set_item('output_path', get_test_output_path('test-copy-temp-frames-file'))
	create_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-copy-temp-frames-file'))
	temp_directory_path = get_temp_directory_path(state_manager.get_temp_path(), get_test_output_path('test-copy-temp-frames-file'))
	copy_file(get_test_example_file('target-240p.jpg'), os.path.join(temp_directory_path, '00000000.png'))
	copy_file(get_test_example_file('target-240p.jpg'), get_test_output_path('test-copy-temp-frames-file'))

	assert copy_temp_frames() == 1

	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-copy-temp-frames'))
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-copy-temp-frames-file'))


def test_finalize_frames() -> None:
	state_manager.set_item('output_path', get_test_output_path('test-finalize-frames'))

	assert finalize_frames(time()) == 1

	create_directory(get_test_output_path('test-finalize-frames'))

	assert finalize_frames(time()) == 1

	copy_file(get_test_example_file('target-240p.jpg'), get_test_output_path(os.path.join('test-finalize-frames', '00000000.jpg')))

	assert finalize_frames(time()) == 0

	copy_file(get_test_example_file('source.mp3'), get_test_output_path(os.path.join('test-finalize-frames', '00000001.mp3')))

	assert finalize_frames(time()) == 1
