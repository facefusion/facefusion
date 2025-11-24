import subprocess

import pytest
from pytest import approx

from facefusion.audio import detect_audio_duration, get_audio_frame, read_static_audio, restrict_trim_audio_frame
from facefusion.download import conditional_download
from .helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3'
	])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('source.mp3'), get_test_example_file('source.wav') ])


def test_get_audio_frame() -> None:
	assert hasattr(get_audio_frame(get_test_example_file('source.mp3'), 25), '__array_interface__')
	assert hasattr(get_audio_frame(get_test_example_file('source.wav'), 25), '__array_interface__')
	assert get_audio_frame('invalid', 25) is None


def test_read_static_audio() -> None:
	assert len(read_static_audio(get_test_example_file('source.mp3'), 25)) == 280
	assert len(read_static_audio(get_test_example_file('source.wav'), 25)) == 280
	assert read_static_audio('invalid', 25) is None


def test_detect_audio_duration() -> None:
	assert detect_audio_duration(get_test_example_file('source.mp3')) == approx(3.788, rel = 1e-3)
	assert detect_audio_duration(get_test_example_file('source.wav')) == approx(3.788, rel = 1e-3)
	assert detect_audio_duration('invalid') == 0


def test_restrict_trim_audio_frame() -> None:
	assert restrict_trim_audio_frame(get_test_example_file('source.mp3'), 25, 0, 50) == (0, 50)
	assert restrict_trim_audio_frame(get_test_example_file('source.mp3'), 25, 20, 95) == (20, 95)
	assert restrict_trim_audio_frame(get_test_example_file('source.mp3'), 25, -10, None) == (0, 95)
	assert restrict_trim_audio_frame(get_test_example_file('source.mp3'), 25, None, -10) == (0, 0)
	assert restrict_trim_audio_frame(get_test_example_file('source.mp3'), 25, 100, None) == (95, 95)
	assert restrict_trim_audio_frame(get_test_example_file('source.mp3'), 25, None, 100) == (0, 95)
	assert restrict_trim_audio_frame(get_test_example_file('source.mp3'), 25, None, None) == (0, 95)
