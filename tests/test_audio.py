import subprocess

import pytest

from facefusion.audio import count_audio_frame_total, detect_audio_duration, get_audio_frame, predict_audio_frame_total, read_static_audio
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
	assert detect_audio_duration(get_test_example_file('source.mp3')) > 3.5
	assert detect_audio_duration(get_test_example_file('source.mp3')) < 4.0
	assert detect_audio_duration(get_test_example_file('source.wav')) > 3.5
	assert detect_audio_duration(get_test_example_file('source.wav')) < 4.0
	assert detect_audio_duration('invalid') == 0


def test_count_audio_frame_total() -> None:
	assert count_audio_frame_total(get_test_example_file('source.mp3'), 25) == 95
	assert count_audio_frame_total(get_test_example_file('source.wav'), 25) == 95
	assert count_audio_frame_total(get_test_example_file('source.mp3'), 12.5) == 48
	assert count_audio_frame_total('invalid', 25) == 0


def test_predict_audio_frame_total() -> None:
	assert predict_audio_frame_total(get_test_example_file('source.mp3'), 25, 0, 95) == 95
	assert predict_audio_frame_total(get_test_example_file('source.mp3'), 25, 0, 50) == 50
	assert predict_audio_frame_total(get_test_example_file('source.mp3'), 12.5, 0, 48) == 48
	assert predict_audio_frame_total(get_test_example_file('source.wav'), 25, 25, 75) == 50
	assert predict_audio_frame_total('invalid', 25, 0, 100) == 0
