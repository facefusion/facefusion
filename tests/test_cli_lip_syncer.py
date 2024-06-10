import subprocess
import sys
import pytest

from facefusion.download import conditional_download
from .helper import get_test_examples_directory, prepare_test_output_directory, get_test_example_file, get_test_output_file, is_test_output_file


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vframes', '1', get_test_example_file('target-240p.jpg') ])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	prepare_test_output_directory()


def test_sync_lip_to_image() -> None:
	commands = [ sys.executable, 'run.py', '--frame-processors', 'lip_syncer', '-s', get_test_example_file('source.mp3'), '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_file('test_sync_lip_to_image.jpg'), '--headless' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test_sync_lip_to_image.jpg') is True


def test_sync_lip_to_video() -> None:
	commands = [ sys.executable, 'run.py', '--frame-processors', 'lip_syncer', '-s', get_test_example_file('source.mp3'), '-t', get_test_example_file('target-240p.mp4'), '-o', get_test_output_file('test_sync_lip_to_video.mp4'), '--trim-frame-end', '10', '--headless' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test_sync_lip_to_video.mp4') is True
