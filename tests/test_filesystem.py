import os.path

import pytest

from facefusion.common_helper import is_windows
from facefusion.download import conditional_download
from facefusion.filesystem import copy_file, create_directory, filter_audio_paths, filter_image_paths, get_file_size, has_audio, has_image, in_directory, is_audio, is_directory, is_file, is_image, is_video, list_directory, remove_directory, same_file_extension, sanitize_path_for_windows
from .helper import get_test_example_file, get_test_examples_directory, get_test_outputs_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])
	copy_file(get_test_example_file('source.jpg'), get_test_example_file('söurce.jpg'))


def test_get_file_size() -> None:
	assert get_file_size(get_test_example_file('source.jpg')) > 0
	assert get_file_size('invalid') == 0


def test_same_file_extension() -> None:
	assert same_file_extension([ 'target.jpg', 'output.jpg' ]) is True
	assert same_file_extension([ 'target.jpg', 'output.mp4' ]) is False


def test_is_file() -> None:
	assert is_file(get_test_example_file('source.jpg')) is True
	assert is_file(get_test_examples_directory()) is False
	assert is_file('invalid') is False


def test_is_directory() -> None:
	assert is_directory(get_test_examples_directory()) is True
	assert is_directory(get_test_example_file('source.jpg')) is False
	assert is_directory('invalid') is False


def test_in_directory() -> None:
	assert in_directory(get_test_example_file('source.jpg')) is True
	assert in_directory('source.jpg') is False
	assert in_directory('invalid') is False


def test_is_audio() -> None:
	assert is_audio(get_test_example_file('source.mp3')) is True
	assert is_audio(get_test_example_file('source.jpg')) is False
	assert is_audio('invalid') is False


def test_has_audio() -> None:
	assert has_audio([ get_test_example_file('source.mp3') ]) is True
	assert has_audio([ get_test_example_file('source.mp3'), get_test_example_file('source.jpg') ]) is True
	assert has_audio([ get_test_example_file('source.jpg'), get_test_example_file('source.jpg') ]) is False
	assert has_audio([ 'invalid' ]) is False


def test_is_image() -> None:
	assert is_image(get_test_example_file('source.jpg')) is True
	assert is_image(get_test_example_file('target-240p.mp4')) is False
	assert is_image('invalid') is False


def test_has_image() -> None:
	assert has_image([ get_test_example_file('source.jpg') ]) is True
	assert has_image([ get_test_example_file('source.jpg'), get_test_example_file('source.mp3') ]) is True
	assert has_image([ get_test_example_file('source.mp3'), get_test_example_file('source.mp3') ]) is False
	assert has_image([ 'invalid' ]) is False


def test_is_video() -> None:
	assert is_video(get_test_example_file('target-240p.mp4')) is True
	assert is_video(get_test_example_file('source.jpg')) is False
	assert is_video('invalid') is False


def test_filter_audio_paths() -> None:
	assert filter_audio_paths([ get_test_example_file('source.jpg'), get_test_example_file('source.mp3') ]) == [ get_test_example_file('source.mp3') ]
	assert filter_audio_paths([ get_test_example_file('source.jpg'), get_test_example_file('source.jpg') ]) == []
	assert filter_audio_paths([ 'invalid' ]) == []


def test_filter_image_paths() -> None:
	assert filter_image_paths([ get_test_example_file('source.jpg'), get_test_example_file('source.mp3') ]) == [ get_test_example_file('source.jpg') ]
	assert filter_image_paths([ get_test_example_file('source.mp3'), get_test_example_file('source.mp3') ]) == []
	assert filter_audio_paths([ 'invalid' ]) == []


def test_sanitize_path_for_windows() -> None:
	if is_windows():
		assert sanitize_path_for_windows(get_test_example_file('söurce.jpg')).endswith('SURCE~1.JPG')
		assert sanitize_path_for_windows('invalid') is None


def test_create_directory() -> None:
	create_directory_path = os.path.join(get_test_outputs_directory(), 'create_directory')

	assert create_directory(create_directory_path) is True
	assert create_directory(get_test_example_file('source.jpg')) is False


def test_list_directory() -> None:
	assert list_directory(get_test_examples_directory())
	assert list_directory(get_test_example_file('source.jpg')) is None
	assert list_directory('invalid') is None


def test_remove_directory() -> None:
	remove_directory_path = os.path.join(get_test_outputs_directory(), 'remove_directory')
	create_directory(remove_directory_path)

	assert remove_directory(remove_directory_path) is True
	assert remove_directory(get_test_example_file('source.jpg')) is False
	assert remove_directory('invalid') is False
