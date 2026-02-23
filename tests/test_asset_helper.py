import pytest

from facefusion.apis.asset_helper import detect_media_type, extract_audio_metadata, extract_image_metadata, extract_video_metadata
from facefusion.download import conditional_download
from .helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])


def test_detect_media_type() -> None:
	assert detect_media_type(get_test_example_file('source.jpg')) == 'image'
	assert detect_media_type(get_test_example_file('target-240p.mp4')) == 'video'
	assert detect_media_type(get_test_example_file('source.mp3')) == 'audio'


def test_extract_image_metadata() -> None:
	metadata = extract_image_metadata(get_test_example_file('source.jpg'))

	assert metadata.get('resolution') == (1024, 1024)


def test_extract_video_metadata() -> None:
	metadata = extract_video_metadata(get_test_example_file('target-240p.mp4'))

	assert metadata.get('duration') == 10.8
	assert metadata.get('frame_total') == 270
	assert metadata.get('fps') == 25.0
	assert metadata.get('resolution') == (426, 226)


def test_extract_audio_metadata() -> None:
	metadata = extract_audio_metadata(get_test_example_file('source.mp3'))

	assert metadata.get('duration') == 3.7877708333333335
	assert metadata.get('sample_rate') == 44100
	assert metadata.get('channels') == 1
