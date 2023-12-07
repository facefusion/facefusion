import subprocess
import sys
import pytest

from facefusion import wording
from facefusion.download import conditional_download


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download('.assets/examples',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-1080p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-1080p.mp4', '-vframes', '1', '.assets/examples/target-1080p.jpg' ])


def test_image_to_image() -> None:
	commands = [ sys.executable, 'run.py', '-s', '.assets/examples/source.jpg', '-t', '.assets/examples/target-1080p.jpg', '-o', '.assets/examples', '--headless' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert wording.get('processing_image_succeed') in run.stdout.decode()


def test_image_to_video() -> None:
	commands = [ sys.executable, 'run.py', '-s', '.assets/examples/source.jpg', '-t', '.assets/examples/target-1080p.mp4', '-o', '.assets/examples', '--trim-frame-end', '10', '--headless' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert wording.get('processing_video_succeed') in run.stdout.decode()
