import subprocess

import pytest

from facefusion import process_manager
from facefusion.download import conditional_download
from facefusion.ffprobe import detect_audio_channel_total, detect_audio_frame_total, detect_audio_sample_rate
from .helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3'
	])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('source.mp3'), '-t', '1.9', '-ar', '48000', '-ac', '2', get_test_example_file('test-audio-entries.wav') ])


def test_detect_audio_sample_rate() -> None:
	assert detect_audio_sample_rate(get_test_example_file('source.mp3')) == 44100
	assert detect_audio_sample_rate(get_test_example_file('test-audio-entries.wav')) == 48000
	assert detect_audio_sample_rate(get_test_example_file('invalid.mp3')) is None


def test_detect_audio_channel_total() -> None:
	assert detect_audio_channel_total(get_test_example_file('source.mp3')) == 1
	assert detect_audio_channel_total(get_test_example_file('test-audio-entries.wav')) == 2
	assert detect_audio_channel_total(get_test_example_file('invalid.mp3')) is None


def test_detect_audio_frame_total() -> None:
	assert detect_audio_frame_total(get_test_example_file('source.mp3')) == 167039
	assert detect_audio_frame_total(get_test_example_file('test-audio-entries.wav')) == 91200
	assert detect_audio_frame_total(get_test_example_file('invalid.mp3')) is None
