import os.path
import tempfile

import pytest

from facefusion import state_manager
from facefusion.download import conditional_download
from facefusion.filesystem import copy_file, is_directory, is_file
from facefusion.temp_helper import clear_temp_directory, create_temp_directory, get_temp_directory_path, get_temp_file_path, get_temp_frames_pattern, move_temp_file, resolve_temp_frame_paths, resolve_temp_frame_set
from .assert_helper import get_test_example_file, get_test_examples_directory, get_test_output_path, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('temp_frame_format', 'png')

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	prepare_test_output_directory()
	clear_temp_directory(state_manager.get_temp_path(), get_test_output_path('test-temp-helper.mp4'))


def test_get_temp_file_path() -> None:
	state_manager.init_item('output_path', 'temp.mp4')
	assert get_temp_file_path(state_manager.get_temp_path(), get_test_example_file('target-240p.mp4')) == os.path.join(state_manager.get_temp_path(), 'facefusion', 'target-240p', 'temp.mp4')
	assert get_temp_file_path(state_manager.get_temp_path(), get_test_output_path('test-temp-helper.webm')) == os.path.join(state_manager.get_temp_path(), 'facefusion', 'test-temp-helper', 'temp.webm')


def test_move_temp_file() -> None:
	output_path = get_test_output_path('test-temp-helper.mp4')
	create_temp_directory(state_manager.get_temp_path(), output_path)
	copy_file(get_test_example_file('target-240p.mp4'), get_temp_file_path(state_manager.get_temp_path(), output_path))

	assert move_temp_file(state_manager.get_temp_path(), output_path) is True
	assert is_file(get_temp_file_path(state_manager.get_temp_path(), output_path)) is False
	assert is_file(output_path) is True
	assert move_temp_file(state_manager.get_temp_path(), output_path) is False


def test_resolve_temp_frame_paths() -> None:
	output_path = get_test_output_path('test-temp-helper.mp4')
	temp_directory_path = get_temp_directory_path(state_manager.get_temp_path(), output_path)

	assert resolve_temp_frame_paths(state_manager.get_temp_path(), output_path, 'png') == []

	create_temp_directory(state_manager.get_temp_path(), output_path)
	copy_file(get_test_example_file('target-240p.mp4'), get_temp_file_path(state_manager.get_temp_path(), output_path))

	for temp_frame_name in [ '00000001.png', '00000000.png', '00000000.jpg' ]:
		copy_file(get_test_example_file('target-240p.mp4'), os.path.join(temp_directory_path, temp_frame_name))

	assert resolve_temp_frame_paths(state_manager.get_temp_path(), output_path, 'png') ==\
	[
		os.path.join(temp_directory_path, '00000000.png'),
		os.path.join(temp_directory_path, '00000001.png')
	]
	assert resolve_temp_frame_paths(state_manager.get_temp_path(), output_path, 'jpg') ==\
	[
		os.path.join(temp_directory_path, '00000000.jpg')
	]


def test_resolve_temp_frame_set() -> None:
	output_path = get_test_output_path('test-temp-helper.mp4')
	temp_directory_path = get_temp_directory_path(state_manager.get_temp_path(), output_path)

	assert resolve_temp_frame_set(state_manager.get_temp_path(), output_path, 'png') == {}

	create_temp_directory(state_manager.get_temp_path(), output_path)
	copy_file(get_test_example_file('target-240p.mp4'), get_temp_file_path(state_manager.get_temp_path(), output_path))

	for temp_frame_name in [ '00000125.png', '00000124.png', '00000000.png', '00000050.jpg' ]:
		copy_file(get_test_example_file('target-240p.mp4'), os.path.join(temp_directory_path, temp_frame_name))

	assert resolve_temp_frame_set(state_manager.get_temp_path(), output_path, 'png') ==\
	{
		0: os.path.join(temp_directory_path, '00000000.png'),
		124: os.path.join(temp_directory_path, '00000124.png'),
		125: os.path.join(temp_directory_path, '00000125.png')
	}


def test_get_temp_frames_pattern() -> None:
	assert get_temp_frames_pattern(state_manager.get_temp_path(), get_test_example_file('target-240p.mp4'), state_manager.get_item('temp_frame_format'), '%04d') == os.path.join(state_manager.get_temp_path(), 'facefusion', 'target-240p', '%04d.png')
	assert get_temp_frames_pattern(state_manager.get_temp_path(), get_test_example_file('target-240p.mp4'), 'jpg', '*') == os.path.join(state_manager.get_temp_path(), 'facefusion', 'target-240p', '*.jpg')


def test_get_temp_directory_path() -> None:
	assert get_temp_directory_path(state_manager.get_temp_path(), get_test_example_file('target-240p.mp4')) == os.path.join(state_manager.get_temp_path(), 'facefusion', 'target-240p')


def test_create_temp_directory() -> None:
	output_path = get_test_output_path('test-temp-helper.mp4')

	assert create_temp_directory(state_manager.get_temp_path(), output_path) is True
	assert is_directory(get_temp_directory_path(state_manager.get_temp_path(), output_path)) is True
	assert create_temp_directory(state_manager.get_temp_path(), output_path) is True


def test_clear_temp_directory() -> None:
	output_path = get_test_output_path('test-temp-helper.mp4')
	create_temp_directory(state_manager.get_temp_path(), output_path)
	copy_file(get_test_example_file('target-240p.mp4'), get_temp_file_path(state_manager.get_temp_path(), output_path))

	assert clear_temp_directory(state_manager.get_temp_path(), output_path) is True
	assert is_directory(get_temp_directory_path(state_manager.get_temp_path(), output_path)) is False
	assert clear_temp_directory(state_manager.get_temp_path(), output_path) is False
