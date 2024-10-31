import subprocess
import sys

import pytest

from facefusion.download import conditional_download
from facefusion.jobs.job_manager import clear_jobs, init_jobs
from .helper import get_test_example_file, get_test_examples_directory, get_test_jobs_directory, get_test_output_file, is_test_output_file, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vframes', '1', '-vf', 'hue=s=0', get_test_example_file('target-240p-0sat.jpg') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vf', 'hue=s=0', get_test_example_file('target-240p-0sat.mp4') ])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(get_test_jobs_directory())
	prepare_test_output_directory()


def test_colorize_frame_to_image() -> None:
	commands = [ sys.executable, 'facefusion.py', 'headless-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'frame_colorizer', '-t', get_test_example_file('target-240p-0sat.jpg'), '-o', get_test_output_file('test_colorize-frame-to-image.jpg') ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test_colorize-frame-to-image.jpg') is True


def test_colorize_frame_to_video() -> None:
	commands = [ sys.executable, 'facefusion.py', 'headless-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'frame_colorizer', '-t', get_test_example_file('target-240p-0sat.mp4'), '-o', get_test_output_file('test-colorize-frame-to-video.mp4'), '--trim-frame-end', '1' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-colorize-frame-to-video.mp4') is True
