import pytest

from facefusion.apis.asset_helper import detect_media_type_by_path, extract_image_metadata
from facefusion.download import conditional_download
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])


def test_detect_media_type() -> None:
	assert detect_media_type_by_path(get_test_example_file('source.jpg')) == 'image'
	assert detect_media_type_by_path(get_test_example_file('target-240p.mp4')) == 'video'
	assert detect_media_type_by_path(get_test_example_file('source.mp3')) == 'audio'


def test_extract_image_metadata() -> None:
	image_metadata = extract_image_metadata(get_test_example_file('source.jpg'))

	assert image_metadata.get('resolution') == (1024, 1024)
