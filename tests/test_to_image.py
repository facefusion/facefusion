import tempfile
from time import time
from unittest.mock import patch

import pytest

from facefusion import ffmpeg, ffmpeg_builder, process_manager, state_manager
from facefusion.download import conditional_download
from facefusion.temp_helper import clear_temp_directory, create_temp_directory, get_temp_file_path
from facefusion.vision import detect_image_resolution
from facefusion.workflows.to_image import analyse_image, finalize_image, prepare_image, process_image
from .assert_helper import get_test_example_file, get_test_examples_directory, get_test_output_path, is_test_output_file, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
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
	state_manager.init_item('source_paths', [ get_test_example_file('source.jpg') ])
	state_manager.init_item('target_path', get_test_example_file('target-240p.jpg'))
	state_manager.init_item('workflow_mode', 'image-to-image')
	state_manager.init_item('output_image_quality', 100)
	state_manager.init_item('output_image_scale', 1.0)
	state_manager.init_item('processors', [])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	prepare_test_output_directory()


def test_analyse_image() -> None:
	with patch('facefusion.content_analyser.analyse_image', return_value = True) as analyse_image_mock:
		assert analyse_image() == 3

	analyse_image_mock.assert_called_once_with(get_test_example_file('target-240p.jpg'))

	with patch('facefusion.content_analyser.analyse_image', return_value = False):
		assert analyse_image() == 0


def test_prepare_image() -> None:
	state_manager.set_item('output_path', get_test_output_path('test-prepare-image.jpg'))
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-prepare-image.jpg'))
	process_manager.start()

	assert prepare_image() == 1
	assert process_manager.is_pending() is True

	create_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-prepare-image.jpg'))
	state_manager.set_item('output_image_scale', 0.5)
	process_manager.start()

	assert prepare_image() == 0
	assert detect_image_resolution(get_temp_file_path(state_manager.get_temp_path(), get_test_output_path('test-prepare-image.jpg'))) == (212, 112)

	state_manager.set_item('output_image_scale', 2.0)

	assert prepare_image() == 0
	assert detect_image_resolution(get_temp_file_path(state_manager.get_temp_path(), get_test_output_path('test-prepare-image.jpg'))) == (426, 226)

	process_manager.end()
	state_manager.set_item('output_image_scale', 1.0)
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-prepare-image.jpg'))


def test_process_image() -> None:
	state_manager.set_item('output_path', get_test_output_path('test-process-image.jpg'))
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-process-image.jpg'))
	create_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-process-image.jpg'))
	process_manager.start()
	prepare_image()

	assert process_image() == 0

	process_manager.end()

	assert process_image() == 4

	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-process-image.jpg'))


def test_finalize_image() -> None:
	state_manager.set_item('output_path', get_test_output_path('test-finalize-image.jpg'))
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-finalize-image.jpg'))

	assert finalize_image(time()) == 1
	assert is_test_output_file('test-finalize-image.jpg') is False

	create_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-finalize-image.jpg'))
	process_manager.start()
	prepare_image()
	state_manager.set_item('output_image_scale', 2.0)

	assert finalize_image(time()) == 0
	assert detect_image_resolution(get_test_output_path('test-finalize-image.jpg')) == (852, 452)

	process_manager.end()
	state_manager.set_item('output_image_scale', 1.0)
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-finalize-image.jpg'))
