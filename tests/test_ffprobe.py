import subprocess

import pytest

from facefusion import process_manager
from facefusion.download import conditional_download
from facefusion.ffprobe import extract_audio_metadata, extract_video_metadata
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('source.mp3'), '-t', '1.9', '-ar', '48000', '-ac', '2', get_test_example_file('source-48000khz-2ch.wav') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-t', '1', get_test_example_file('target-240p-1s.mov') ])


def test_extract_audio_metadata() -> None:
	audio_metadata = extract_audio_metadata(get_test_example_file('source.mp3'))

	assert audio_metadata.get('sample_rate') == 44100
	assert audio_metadata.get('channel_total') == 1
	assert audio_metadata.get('frame_total') == 167039
	assert audio_metadata.get('bit_rate') == 128000

	audio_metadata = extract_audio_metadata(get_test_example_file('source-48000khz-2ch.wav'))

	assert audio_metadata.get('sample_rate') == 48000
	assert audio_metadata.get('channel_total') == 2
	assert audio_metadata.get('frame_total') == 91200
	assert audio_metadata.get('bit_rate') == 1536000


def test_extract_video_metadata() -> None:
	video_metadata = extract_video_metadata(get_test_example_file('target-240p.mp4'))

	assert video_metadata.get('fps') == 25.0
	assert video_metadata.get('duration') == 10.8
	assert video_metadata.get('resolution') == (426, 226)
	assert video_metadata.get('bit_rate') == 138754

	video_metadata = extract_video_metadata(get_test_example_file('target-240p-1s.mov'))

	assert video_metadata.get('fps') == 25.0
	assert video_metadata.get('duration') == 1.0
	assert video_metadata.get('resolution') == (426, 226)
	assert video_metadata.get('bit_rate') == 165600
