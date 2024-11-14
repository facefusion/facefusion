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
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vframes', '1', get_test_example_file('target-240p-batch-1.jpg') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vframes', '2', get_test_example_file('target-240p-batch-2.jpg') ])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(get_test_jobs_directory())
	prepare_test_output_directory()


def test_batch_run_targets() -> None:
	commands = [ sys.executable, 'facefusion.py', 'batch-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', get_test_example_file('target-240p-batch-*.jpg'), '-o', get_test_output_file('test-batch-run-targets-{index}.jpg') ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-batch-run-targets-0.jpg') is True
	assert is_test_output_file('test-batch-run-targets-1.jpg') is True
	assert is_test_output_file('test-batch-run-targets-2.jpg') is False


def test_batch_run_sources_to_targets() -> None:
	commands = [ sys.executable, 'facefusion.py', 'batch-run', '--jobs-path', get_test_jobs_directory(), '-s', get_test_example_file('target-240p-batch-*.jpg'), '-t', get_test_example_file('target-240p-batch-*.jpg'), '-o', get_test_output_file('test-batch-run-sources-to-targets-{index}.jpg') ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-batch-run-sources-to-targets-0.jpg') is True
	assert is_test_output_file('test-batch-run-sources-to-targets-1.jpg') is True
	assert is_test_output_file('test-batch-run-sources-to-targets-2.jpg') is True
	assert is_test_output_file('test-batch-run-sources-to-targets-3.jpg') is True
	assert is_test_output_file('test-batch-run-sources-to-targets-4.jpg') is False
