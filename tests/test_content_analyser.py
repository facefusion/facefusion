from unittest.mock import patch

import pytest

from facefusion import content_analyser, content_store, inference_manager, process_manager, state_manager, store_creator
from facefusion.content_analyser import analyse_frame, analyse_image, analyse_stream, override_inference_providers
from facefusion.download import conditional_download
from facefusion.session_context import get_session_id
from facefusion.vision import read_static_image
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	inference_manager.init()

	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg'
	])

	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github' ])

	content_analyser.pre_check()


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	content_store.clear()


def test_override_inference_providers() -> None:
	assert override_inference_providers() == []

	with patch('facefusion.content_analyser.is_macos', return_value = True):
		with patch('facefusion.content_analyser.has_execution_provider', return_value = True):
			assert override_inference_providers() == [ 'CPUExecutionProvider' ]


def test_analyse_frame() -> None:
	assert analyse_frame(read_static_image(get_test_example_file('source.jpg'))) is False
	assert analyse_frame(None) is False


def test_analyse_image() -> None:
	assert analyse_image(get_test_example_file('source.jpg')) is False
	assert analyse_image('invalid') is False


def test_analyse_stream() -> None:
	vision_frame = read_static_image(get_test_example_file('source.jpg'))

	for _ in range(30):
		assert analyse_stream(vision_frame) is False

	assert store_creator.get_content(content_store.CONTENT_STORE, get_session_id()) == { 'hit': 0, 'total': 30 }

	content_store.set_hit()

	assert analyse_stream(vision_frame) is True
