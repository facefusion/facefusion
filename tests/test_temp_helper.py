import os.path
import tempfile

import pytest

import facefusion.globals
from facefusion.download import conditional_download
from facefusion.temp_helper import get_temp_file_path, get_temp_directory_path, get_temp_frame_paths, get_temp_frames_pattern


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download('.assets/examples',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4'
	])
	facefusion.globals.temp_frame_format = 'png'


def test_get_temp_file_path() -> None:
	temp_directory = tempfile.gettempdir()
	assert get_temp_file_path('.assets/examples/target-240p.mp4') == os.path.join(temp_directory, 'facefusion/target-240p/temp.mp4')


def test_get_temp_directory_path() -> None:
	temp_directory = tempfile.gettempdir()
	assert get_temp_directory_path('.assets/examples/target-240p.mp4') == os.path.join(temp_directory, 'facefusion/target-240p')


def test_get_temp_frames_pattern() -> None:
	temp_directory = tempfile.gettempdir()
	assert get_temp_frames_pattern('.assets/examples/target-240p.mp4', '%04d') == os.path.join(temp_directory, '/tmp/facefusion/target-240p/%04d.png')
