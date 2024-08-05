import pytest

from facefusion.download import conditional_download, get_download_size, is_download_done
from .helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])


def test_get_download_size() -> None:
	assert get_download_size('https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4') == 191675
	assert get_download_size('https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-360p.mp4') == 370732
	assert get_download_size('invalid') == 0


def test_is_download_done() -> None:
	assert is_download_done('https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4', get_test_example_file('target-240p.mp4')) is True
	assert is_download_done('https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4', 'invalid') is False
	assert is_download_done('invalid', 'invalid') is False
