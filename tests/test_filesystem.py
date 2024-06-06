import shutil
import pytest

from facefusion.common_helper import is_windows
from facefusion.download import conditional_download
from facefusion.filesystem import get_file_size, is_file, is_directory, is_audio, has_audio, is_image, has_image, is_video, filter_audio_paths, filter_image_paths, list_directory, sanitize_path_for_windows


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download('.assets/examples',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4'
	])
	shutil.copyfile('.assets/examples/source.jpg', '.assets/examples/söurce.jpg')


def test_get_file_size() -> None:
	assert get_file_size('.assets/examples/source.jpg') > 0
	assert get_file_size('invalid') == 0


def test_is_file() -> None:
	assert is_file('.assets/examples/source.jpg') is True
	assert is_file('.assets/examples') is False
	assert is_file('invalid') is False


def test_is_directory() -> None:
	assert is_directory('.assets/examples') is True
	assert is_directory('.assets/examples/source.jpg') is False
	assert is_directory('invalid') is False


def test_is_audio() -> None:
	assert is_audio('.assets/examples/source.mp3') is True
	assert is_audio('.assets/examples/source.jpg') is False
	assert is_audio('invalid') is False


def test_has_audio() -> None:
	assert has_audio([ '.assets/examples/source.mp3' ]) is True
	assert has_audio([ '.assets/examples/source.mp3', '.assets/examples/source.jpg' ]) is True
	assert has_audio([ '.assets/examples/source.jpg', '.assets/examples/source.jpg' ]) is False
	assert has_audio([ 'invalid' ]) is False


def test_is_image() -> None:
	assert is_image('.assets/examples/source.jpg') is True
	assert is_image('.assets/examples/target-240p.mp4') is False
	assert is_image('invalid') is False


def test_has_image() -> None:
	assert has_image([ '.assets/examples/source.jpg' ]) is True
	assert has_image([ '.assets/examples/source.jpg', '.assets/examples/source.mp3' ]) is True
	assert has_image([ '.assets/examples/source.mp3', '.assets/examples/source.mp3' ]) is False
	assert has_image([ 'invalid' ]) is False


def test_is_video() -> None:
	assert is_video('.assets/examples/target-240p.mp4') is True
	assert is_video('.assets/examples/source.jpg') is False
	assert is_video('invalid') is False


def test_filter_audio_paths() -> None:
	assert filter_audio_paths([ '.assets/examples/source.jpg', '.assets/examples/source.mp3' ]) == [ '.assets/examples/source.mp3' ]
	assert filter_audio_paths([ '.assets/examples/source.jpg', '.assets/examples/source.jpg' ]) == []
	assert filter_audio_paths([ 'invalid' ]) == []


def test_filter_image_paths() -> None:
	assert filter_image_paths([ '.assets/examples/source.jpg', '.assets/examples/source.mp3' ]) == [ '.assets/examples/source.jpg' ]
	assert filter_image_paths([ '.assets/examples/source.mp3', '.assets/examples/source.mp3' ]) == []
	assert filter_audio_paths([ 'invalid' ]) == []


def test_list_directory() -> None:
	assert list_directory('.assets/examples')
	assert list_directory('.assets/examples/source.jpg') is None
	assert list_directory('invalid') is None


@pytest.mark.skip()
def test_sanitize_path_for_windows() -> None:
	if is_windows():
		assert sanitize_path_for_windows('.assets/examples/söurce.jpg') == 'ASSETS~1/examples/SURCE~1.JPG'
		assert sanitize_path_for_windows('invalid') is None
