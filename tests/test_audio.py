import subprocess
<<<<<<< HEAD
=======

>>>>>>> origin/master
import pytest

from facefusion.audio import get_audio_frame, read_static_audio
from facefusion.download import conditional_download
<<<<<<< HEAD
=======
from .helper import get_test_example_file, get_test_examples_directory
>>>>>>> origin/master


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
<<<<<<< HEAD
	conditional_download('.assets/examples',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.mp3'
	])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/source.mp3', '.assets/examples/source.wav' ])


def test_get_audio_frame() -> None:
	assert get_audio_frame('.assets/examples/source.mp3', 25) is not None
	assert get_audio_frame('.assets/examples/source.wav', 25) is not None
=======
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3'
	])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('source.mp3'), get_test_example_file('source.wav') ])


def test_get_audio_frame() -> None:
	assert hasattr(get_audio_frame(get_test_example_file('source.mp3'), 25), '__array_interface__')
	assert hasattr(get_audio_frame(get_test_example_file('source.wav'), 25), '__array_interface__')
>>>>>>> origin/master
	assert get_audio_frame('invalid', 25) is None


def test_read_static_audio() -> None:
<<<<<<< HEAD
	assert len(read_static_audio('.assets/examples/source.mp3', 25)) == 280
	assert len(read_static_audio('.assets/examples/source.wav', 25)) == 280
=======
	assert len(read_static_audio(get_test_example_file('source.mp3'), 25)) == 280
	assert len(read_static_audio(get_test_example_file('source.wav'), 25)) == 280
>>>>>>> origin/master
	assert read_static_audio('invalid', 25) is None
