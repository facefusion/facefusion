import subprocess

import pytest

from facefusion import process_manager
from facefusion.download import conditional_download
from facefusion.ffprobe import detect_audio_channel_total, detect_audio_format, detect_audio_frame_total, detect_audio_sample_rate
from .helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3'
	])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('source.mp3'), get_test_example_file('source.wav') ])


def test_detect_audio_sample_rate() -> None:
	audio_sample_rate = detect_audio_sample_rate(get_test_example_file('source.mp3'))
	assert audio_sample_rate == 44100

	audio_sample_rate = detect_audio_sample_rate(get_test_example_file('source.wav'))
	assert audio_sample_rate == 44100

	audio_sample_rate = detect_audio_sample_rate(get_test_example_file('invalid.mp3'))
	assert audio_sample_rate is None


def test_detect_audio_channel_total() -> None:
	audio_channel_total = detect_audio_channel_total(get_test_example_file('source.mp3'))
	assert audio_channel_total == 1

	audio_channel_total = detect_audio_channel_total(get_test_example_file('source.wav'))
	assert audio_channel_total == 1

	audio_channel_total = detect_audio_channel_total(get_test_example_file('invalid.mp3'))
	assert audio_channel_total is None


def test_detect_audio_frame_total() -> None:
	audio_frame_total = detect_audio_frame_total(get_test_example_file('source.mp3'))
	assert audio_frame_total == 167039

	audio_frame_total = detect_audio_frame_total(get_test_example_file('source.wav'))
	assert audio_frame_total == 167039

	audio_frame_total = detect_audio_frame_total(get_test_example_file('invalid.mp3'))
	assert audio_frame_total is None


def test_detect_audio_format() -> None:
	audio_format = detect_audio_format(get_test_example_file('source.mp3'))
	assert audio_format == 'mp3'

	audio_format = detect_audio_format(get_test_example_file('source.wav'))
	assert audio_format == 'pcm_s16le'

	audio_format = detect_audio_format(get_test_example_file('invalid.mp3'))
	assert audio_format is None
