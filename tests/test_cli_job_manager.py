import subprocess
import sys

import pytest

from facefusion.download import conditional_download
from facefusion.jobs.job_manager import clear_jobs, count_step_total, init_jobs
from .helper import get_test_example_file, get_test_examples_directory, get_test_jobs_directory, get_test_output_file, is_test_job_file


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


@pytest.mark.skip()
def test_job_list() -> None:
	pass


def test_job_create() -> None:
	commands = [ sys.executable, 'facefusion.py', 'job-create', 'test-job-create', '--jobs-path', get_test_jobs_directory() ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_job_file('test-job-create.json', 'drafted') is True

	commands = [ sys.executable, 'facefusion.py', 'job-create', 'test-job-create', '--jobs-path', get_test_jobs_directory() ]

	assert subprocess.run(commands).returncode == 1


def test_job_submit() -> None:
	commands = [ sys.executable, 'facefusion.py', 'job-submit', 'test-job-submit', '--jobs-path', get_test_jobs_directory() ]

	assert subprocess.run(commands).returncode == 1

	commands = [ sys.executable, 'facefusion.py', 'job-create', 'test-job-submit', '--jobs-path', get_test_jobs_directory() ]
	subprocess.run(commands)

	assert subprocess.run(commands).returncode == 1

	commands = [ sys.executable, 'facefusion.py', 'job-add-step', 'test-job-submit', '--jobs-path', get_test_jobs_directory(), '-s', get_test_example_file('source.jpg'), '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_file('test-job-remix-step.jpg') ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-submit', 'test-job-submit', '--jobs-path', get_test_jobs_directory() ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_job_file('test-job-submit.json', 'queued') is True
	assert subprocess.run(commands).returncode == 1


def test_submit_all() -> None:
	commands = [ sys.executable, 'facefusion.py', 'job-submit-all', '--jobs-path', get_test_jobs_directory(), '--halt-on-error' ]

	assert subprocess.run(commands).returncode == 1

	commands = [ sys.executable, 'facefusion.py', 'job-create', 'test-job-submit-all-1', '--jobs-path', get_test_jobs_directory() ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-create', 'test-job-submit-all-2', '--jobs-path', get_test_jobs_directory() ]
	subprocess.run(commands)

	assert subprocess.run(commands).returncode == 1

	commands = [ sys.executable, 'facefusion.py', 'job-add-step', 'test-job-submit-all-1', '--jobs-path', get_test_jobs_directory(), '-s', get_test_example_file('source.jpg'), '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_file('test-job-remix-step.jpg') ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-add-step', 'test-job-submit-all-2', '--jobs-path', get_test_jobs_directory(), '-s', get_test_example_file('source.jpg'), '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_file('test-job-remix-step.jpg') ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-submit-all', '--jobs-path', get_test_jobs_directory(), '--halt-on-error' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_job_file('test-job-submit-all-1.json', 'queued') is True
	assert is_test_job_file('test-job-submit-all-2.json', 'queued') is True
	assert subprocess.run(commands).returncode == 1


def test_job_delete() -> None:
	commands = [ sys.executable, 'facefusion.py', 'job-delete', 'test-job-delete', '--jobs-path', get_test_jobs_directory() ]

	assert subprocess.run(commands).returncode == 1

	commands = [ sys.executable, 'facefusion.py', 'job-create', 'test-job-delete', '--jobs-path', get_test_jobs_directory() ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-delete', 'test-job-delete', '--jobs-path', get_test_jobs_directory() ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_job_file('test-job-delete.json', 'drafted') is False
	assert subprocess.run(commands).returncode == 1


def test_job_delete_all() -> None:
	commands = [ sys.executable, 'facefusion.py', 'job-delete-all', '--jobs-path', get_test_jobs_directory(), '--halt-on-error' ]

	assert subprocess.run(commands).returncode == 1

	commands = [ sys.executable, 'facefusion.py', 'job-create', 'test-job-delete-all-1', '--jobs-path', get_test_jobs_directory() ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-create', 'test-job-delete-all-2', '--jobs-path', get_test_jobs_directory() ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-delete-all', '--jobs-path', get_test_jobs_directory(), '--halt-on-error' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_job_file('test-job-delete-all-1.json', 'drafted') is False
	assert is_test_job_file('test-job-delete-all-2.json', 'drafted') is False
	assert subprocess.run(commands).returncode == 1


def test_job_add_step() -> None:
	commands = [ sys.executable, 'facefusion.py', 'job-add-step', 'test-job-add-step', '--jobs-path', get_test_jobs_directory(), '-s', get_test_example_file('source.jpg'), '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_file('test-job-remix-step.jpg') ]

	assert subprocess.run(commands).returncode == 1
	assert count_step_total('test-job-add-step') == 0

	commands = [ sys.executable, 'facefusion.py', 'job-create', 'test-job-add-step', '--jobs-path', get_test_jobs_directory() ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-add-step', 'test-job-add-step', '--jobs-path', get_test_jobs_directory(), '-s', get_test_example_file('source.jpg'), '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_file('test-job-remix-step.jpg') ]

	assert subprocess.run(commands).returncode == 0
	assert count_step_total('test-job-add-step') == 1


def test_job_remix() -> None:
	commands = [ sys.executable, 'facefusion.py', 'job-remix-step', 'test-job-remix-step', '0', '--jobs-path', get_test_jobs_directory(), '-s', get_test_example_file('source.jpg'), '-o', get_test_output_file('test-job-remix-step.jpg') ]

	assert subprocess.run(commands).returncode == 1
	assert count_step_total('test-job-remix-step') == 0

	commands = [ sys.executable, 'facefusion.py', 'job-create', 'test-job-remix-step', '--jobs-path', get_test_jobs_directory() ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-add-step', 'test-job-remix-step', '--jobs-path', get_test_jobs_directory(), '-s', get_test_example_file('source.jpg'), '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_file('test-job-remix-step.jpg') ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-remix-step', 'test-job-remix-step', '0', '--jobs-path', get_test_jobs_directory(), '-s', get_test_example_file('source.jpg'), '-o', get_test_output_file('test-job-remix-step.jpg') ]

	assert count_step_total('test-job-remix-step') == 1
	assert subprocess.run(commands).returncode == 0
	assert count_step_total('test-job-remix-step') == 2

	commands = [ sys.executable, 'facefusion.py', 'job-remix-step', 'test-job-remix-step', '-1', '--jobs-path', get_test_jobs_directory(), '-s', get_test_example_file('source.jpg'), '-o', get_test_output_file('test-job-remix-step.jpg') ]

	assert subprocess.run(commands).returncode == 0
	assert count_step_total('test-job-remix-step') == 3


def test_job_insert_step() -> None:
	commands = [ sys.executable, 'facefusion.py', 'job-insert-step', 'test-job-insert-step', '0', '--jobs-path', get_test_jobs_directory(), '-s', get_test_example_file('source.jpg'), '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_file('test-job-remix-step.jpg') ]

	assert subprocess.run(commands).returncode == 1
	assert count_step_total('test-job-insert-step') == 0

	commands = [ sys.executable, 'facefusion.py', 'job-create', 'test-job-insert-step', '--jobs-path', get_test_jobs_directory() ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-add-step', 'test-job-insert-step', '--jobs-path', get_test_jobs_directory(), '-s', get_test_example_file('source.jpg'), '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_file('test-job-remix-step.jpg') ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-insert-step', 'test-job-insert-step', '0', '--jobs-path', get_test_jobs_directory(), '-s', get_test_example_file('source.jpg'), '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_file('test-job-remix-step.jpg') ]

	assert count_step_total('test-job-insert-step') == 1
	assert subprocess.run(commands).returncode == 0
	assert count_step_total('test-job-insert-step') == 2

	commands = [ sys.executable, 'facefusion.py', 'job-insert-step', 'test-job-insert-step', '-1', '--jobs-path', get_test_jobs_directory(), '-s', get_test_example_file('source.jpg'), '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_file('test-job-remix-step.jpg') ]

	assert subprocess.run(commands).returncode == 0
	assert count_step_total('test-job-insert-step') == 3


def test_job_remove_step() -> None:
	commands = [ sys.executable, 'facefusion.py', 'job-remove-step', 'test-job-remove-step', '0', '--jobs-path', get_test_jobs_directory() ]

	assert subprocess.run(commands).returncode == 1

	commands = [ sys.executable, 'facefusion.py', 'job-create', 'test-job-remove-step', '--jobs-path', get_test_jobs_directory() ]
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-add-step', 'test-job-remove-step', '--jobs-path', get_test_jobs_directory(), '-s', get_test_example_file('source.jpg'), '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_file('test-job-remix-step.jpg') ]
	subprocess.run(commands)
	subprocess.run(commands)

	commands = [ sys.executable, 'facefusion.py', 'job-remove-step', 'test-job-remove-step', '0', '--jobs-path', get_test_jobs_directory() ]

	assert count_step_total('test-job-remove-step') == 2
	assert subprocess.run(commands).returncode == 0
	assert count_step_total('test-job-remove-step') == 1

	commands = [ sys.executable, 'facefusion.py', 'job-remove-step', 'test-job-remove-step', '-1', '--jobs-path', get_test_jobs_directory() ]

	assert subprocess.run(commands).returncode == 0
	assert subprocess.run(commands).returncode == 1
	assert count_step_total('test-job-remove-step') == 0
