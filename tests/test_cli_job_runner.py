import subprocess
import sys

import pytest

from facefusion.download import conditional_download
from facefusion.jobs.job_manager import clear_jobs, init_jobs, move_job_file, set_steps_status
from .helper import get_test_example_file, get_test_examples_directory, get_test_jobs_directory, get_test_output_file, is_test_output_file, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vframes', '1', get_test_example_file('target-240p.jpg') ])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(get_test_jobs_directory())
	prepare_test_output_directory()


def test_job_run() -> None:
	commands = [ sys.executable, 'facefusion.py', 'job-run', 'test-job-run', '--jobs-path', get_test_jobs_directory() ]

	assert subprocess.run(commands).returncode == 1

	commands = [ sys.executable, 'facefusion.py', 'job-create', 'test-job-run', '--jobs-path', get_test_jobs_directory() ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-add-step', 'test-job-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_file('test-job-run.jpg') ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-run', 'test-job-run', '--jobs-path', get_test_jobs_directory() ]

	assert subprocess.run(commands).returncode == 1

	commands = [ sys.executable, 'facefusion.py', 'job-submit', 'test-job-run', '--jobs-path', get_test_jobs_directory() ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-run', 'test-job-run', '--jobs-path', get_test_jobs_directory() ]

	assert subprocess.run(commands).returncode == 0
	assert subprocess.run(commands).returncode == 1
	assert is_test_output_file('test-job-run.jpg') is True


def test_job_run_all() -> None:
	commands = [ sys.executable, 'facefusion.py', 'job-run-all', '--jobs-path', get_test_jobs_directory(), '--halt-on-error' ]

	assert subprocess.run(commands).returncode == 1

	commands = [ sys.executable, 'facefusion.py', 'job-create', 'test-job-run-all-1', '--jobs-path', get_test_jobs_directory() ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-create', 'test-job-run-all-2', '--jobs-path', get_test_jobs_directory() ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-add-step', 'test-job-run-all-1', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_file('test-job-run-all-1.jpg') ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-add-step', 'test-job-run-all-2', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', get_test_example_file('target-240p.mp4'), '-o', get_test_output_file('test-job-run-all-2.mp4'), '--trim-frame-end', '1' ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-add-step', 'test-job-run-all-2', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', get_test_example_file('target-240p.mp4'), '-o', get_test_output_file('test-job-run-all-2.mp4'), '--trim-frame-start', '0', '--trim-frame-end', '1' ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-run-all', '--jobs-path', get_test_jobs_directory(), '--halt-on-error' ]

	assert subprocess.run(commands).returncode == 1

	commands = [ sys.executable, 'facefusion.py', 'job-submit-all', '--jobs-path', get_test_jobs_directory(), '--halt-on-error' ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-run-all', '--jobs-path', get_test_jobs_directory(), '--halt-on-error' ]

	assert subprocess.run(commands).returncode == 0
	assert subprocess.run(commands).returncode == 1
	assert is_test_output_file('test-job-run-all-1.jpg') is True
	assert is_test_output_file('test-job-run-all-2.mp4') is True


def test_job_retry() -> None:
	commands = [ sys.executable, 'facefusion.py', 'job-retry', 'test-job-retry', '--jobs-path', get_test_jobs_directory() ]

	assert subprocess.run(commands).returncode == 1

	commands = [ sys.executable, 'facefusion.py', 'job-create', 'test-job-retry', '--jobs-path', get_test_jobs_directory() ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-add-step', 'test-job-retry', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_file('test-job-retry.jpg') ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-retry', 'test-job-retry', '--jobs-path', get_test_jobs_directory() ]

	assert subprocess.run(commands).returncode == 1

	set_steps_status('test-job-retry', 'failed')
	move_job_file('test-job-retry', 'failed')

	commands = [ sys.executable, 'facefusion.py', 'job-retry', 'test-job-retry', '--jobs-path', get_test_jobs_directory() ]

	assert subprocess.run(commands).returncode == 0
	assert subprocess.run(commands).returncode == 1
	assert is_test_output_file('test-job-retry.jpg') is True


def test_job_retry_all() -> None:
	commands = [ sys.executable, 'facefusion.py', 'job-retry-all', '--jobs-path', get_test_jobs_directory(), '--halt-on-error' ]

	assert subprocess.run(commands).returncode == 1

	commands = [ sys.executable, 'facefusion.py', 'job-create', 'test-job-retry-all-1', '--jobs-path', get_test_jobs_directory() ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-create', 'test-job-retry-all-2', '--jobs-path', get_test_jobs_directory() ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-add-step', 'test-job-retry-all-1', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_file('test-job-retry-all-1.jpg') ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-add-step', 'test-job-retry-all-2', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', get_test_example_file('target-240p.mp4'), '-o', get_test_output_file('test-job-retry-all-2.mp4'), '--trim-frame-end', '1' ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-add-step', 'test-job-retry-all-2', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', get_test_example_file('target-240p.mp4'), '-o', get_test_output_file('test-job-retry-all-2.mp4'), '--trim-frame-start', '0', '--trim-frame-end', '1' ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-retry-all', '--jobs-path', get_test_jobs_directory(), '--halt-on-error' ]

	assert subprocess.run(commands).returncode == 1

	set_steps_status('test-job-retry-all-1', 'failed')
	set_steps_status('test-job-retry-all-2', 'failed')
	move_job_file('test-job-retry-all-1', 'failed')
	move_job_file('test-job-retry-all-2', 'failed')

	commands = [ sys.executable, 'facefusion.py', 'job-retry-all', '--jobs-path', get_test_jobs_directory(), '--halt-on-error' ]

	assert subprocess.run(commands).returncode == 0
	assert subprocess.run(commands).returncode == 1
	assert is_test_output_file('test-job-retry-all-1.jpg') is True
	assert is_test_output_file('test-job-retry-all-2.mp4') is True
