import shutil
import pytest

from facefusion.common_helper import is_windows
from facefusion.download import conditional_download
from facefusion.filesystem import get_file_size, is_file, is_directory, is_audio, has_audio, is_image, has_image, is_video, filter_audio_paths, filter_image_paths, list_directory, sanitize_path_for_windows
from .helper import get_test_examples_directory, get_test_example_file


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4'
	])
	shutil.copyfile(get_test_example_file('source.jpg'), get_test_example_file('söurce.jpg'))


def test_get_file_size() -> None:
	assert get_file_size(get_test_example_file('source.jpg')) > 0
	assert get_file_size('invalid') == 0


def test_is_file() -> None:
	assert is_file(get_test_example_file('source.jpg')) is True
	assert is_file(get_test_examples_directory()) is False
	assert is_file('invalid') is False


def test_is_directory() -> None:
	assert is_directory(get_test_examples_directory()) is True
	assert is_directory(get_test_example_file('source.jpg')) is False
	assert is_directory('invalid') is False


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


def test_list_directory() -> None:
	assert list_directory(get_test_examples_directory())
	assert list_directory(get_test_example_file('source.jpg')) is None
	assert list_directory('invalid') is None


@pytest.mark.skip()
def test_sanitize_path_for_windows() -> None:
	if is_windows():
		assert sanitize_path_for_windows(get_test_example_file('söurce.jpg')).endswith('SURCE~1.JPG')
		assert sanitize_path_for_windows('invalid') is None
