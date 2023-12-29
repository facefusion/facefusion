import pytest

from facefusion.download import conditional_download
from facefusion.filesystem import is_file, is_directory, list_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download('.assets/examples',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.jpg'
	])


def test_is_file() -> None:
	assert is_file('.assets/examples/source.jpg') is True
	assert is_file('.assets/examples') is False
	assert is_file('invalid') is False


def test_is_directory() -> None:
	assert is_directory('.assets/examples') is True
	assert is_directory('.assets/examples/source.jpg') is False
	assert is_directory('invalid') is False


def test_list_directory() -> None:
	assert list_directory('.assets/examples')
	assert list_directory('.assets/examples/source.jpg') is None
	assert list_directory('invalid') is None
