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
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vframes', '1', get_test_example_file('target-240p-a.jpg') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vframes', '2', get_test_example_file('target-240p-b.jpg') ])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(get_test_jobs_directory())
	prepare_test_output_directory()


def test_bulk_run_image_to_image() -> None:
	commands = [ sys.executable, 'facefusion.py', 'bulk-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-s', get_test_example_file('target-240p-*.jpg'), '-t', get_test_example_file('target-240p-*.jpg'), '-o', get_test_output_file('test-bulk-run-image-to-image-{index}.jpg') ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-bulk-run-image-to-image-0.jpg') is True
	assert is_test_output_file('test-bulk-run-image-to-image-1.jpg') is True
	assert is_test_output_file('test-bulk-run-image-to-image-2.jpg') is True
	assert is_test_output_file('test-bulk-run-image-to-image-3.jpg') is True


def test_bulk_run_image_to_video() -> None:
	commands = [ sys.executable, 'facefusion.py', 'bulk-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-s', get_test_example_file('target-240p-*.jpg'), '-t', get_test_example_file('target-240p.mp4'), '-o', get_test_output_file('test-bulk-run-image-to-video-{index}.mp4') ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-bulk-run-image-to-video-0.mp4') is True
	assert is_test_output_file('test-bulk-run-image-to-video-1.mp4') is True
