import subprocess
import sys
import pytest

from facefusion.download import conditional_download
from facefusion.job_manager import clear_jobs, init_jobs, count_step_total
from .helper import get_test_jobs_directory, get_test_examples_directory, prepare_test_output_directory, is_test_job_file, get_test_example_file, get_test_output_file, is_test_output_file


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vframes', '1', get_test_example_file('target-240p.jpg') ])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(get_test_jobs_directory())
	prepare_test_output_directory()


def test_job_run() -> None:
	commands = [ sys.executable, 'run.py', '-j', get_test_jobs_directory(), '--job-run', 'test-job-run' ]

	assert subprocess.run(commands).returncode == 1

	commands = [ sys.executable, 'run.py', '-j', get_test_jobs_directory(), '--job-create', 'test-job-run' ]
	subprocess.run(commands)

	commands = [ sys.executable, 'run.py', '-j', get_test_jobs_directory(), '--job-add-step', 'test-job-run', '--frame-processors', 'face_debugger', '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_file('test-job-run.jpg') ]
	subprocess.run(commands)

	commands = [ sys.executable, 'run.py', '-j', get_test_jobs_directory(), '--job-run', 'test-job-run' ]

	assert subprocess.run(commands).returncode == 1

	commands = [ sys.executable, 'run.py', '-j', get_test_jobs_directory(), '--job-submit', 'test-job-run' ]
	subprocess.run(commands)

	commands = [ sys.executable, 'run.py', '-j', get_test_jobs_directory(), '--job-run', 'test-job-run' ]

	assert subprocess.run(commands).returncode == 0
	assert subprocess.run(commands).returncode == 1
	assert is_test_output_file('test-job-run.jpg') is True


@pytest.mark.skip()
def test_job_run_all() -> None:
	pass


@pytest.mark.skip()
def test_job_retry() -> None:
	pass


@pytest.mark.skip()
def test_job_retry_all() -> None:
	pass
