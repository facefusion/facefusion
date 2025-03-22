import os.path
import tempfile

import pytest

from weyfusion import state_manager
from weyfusion.download import conditional_download
from weyfusion.temp_helper import get_temp_directory_path, get_temp_file_path, get_temp_frames_pattern
from .helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/weyfusion/weyfusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])
	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('temp_frame_format', 'png')


def test_get_temp_file_path() -> None:
	temp_directory = tempfile.gettempdir()
	assert get_temp_file_path(get_test_example_file('target-240p.mp4')) == os.path.join(temp_directory, 'weyfusion', 'target-240p', 'temp.mp4')


def test_get_temp_directory_path() -> None:
	temp_directory = tempfile.gettempdir()
	assert get_temp_directory_path(get_test_example_file('target-240p.mp4')) == os.path.join(temp_directory, 'weyfusion', 'target-240p')


def test_get_temp_frames_pattern() -> None:
	temp_directory = tempfile.gettempdir()
	assert get_temp_frames_pattern(get_test_example_file('target-240p.mp4'), '%04d') == os.path.join(temp_directory, 'weyfusion', 'target-240p', '%04d.png')
