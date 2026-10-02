import os
import tempfile
from time import time

import pytest

from facefusion import ffmpeg, ffmpeg_builder, inference_manager, process_manager, state_manager
from facefusion.download import conditional_download
from facefusion.vision import detect_image_resolution
from facefusion.workflows.image_to_image import process
from .assert_helper import get_test_example_file, get_test_examples_directory, get_test_output_path, is_test_output_file, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()

	inference_manager.init()

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

	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github' ])
	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('source_paths', [ get_test_example_file('source.jpg') ])
	state_manager.init_item('target_path', get_test_example_file('target-240p.jpg'))
	state_manager.init_item('workflow_mode', 'image-to-image')
	state_manager.init_item('output_image_quality', 100)
	state_manager.init_item('output_image_scale', 2.0)
	state_manager.init_item('processors', [])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	prepare_test_output_directory()


def test_process() -> None:
	state_manager.set_item('output_path', get_test_output_path('test-process.jpg'))

	assert process(time()) == 0
	assert detect_image_resolution(get_test_output_path('test-process.jpg')) == (852, 452)
	assert process_manager.is_pending() is True

	state_manager.set_item('output_path', get_test_output_path(os.path.join('invalid', 'test-process.jpg')))

	assert process(time()) == 1
	assert is_test_output_file(os.path.join('invalid', 'test-process.jpg')) is False
	assert process_manager.is_pending() is True
