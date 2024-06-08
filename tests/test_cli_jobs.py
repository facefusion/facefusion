import subprocess
import sys

import pytest

from facefusion.download import conditional_download
from facefusion.job_manager import clear_jobs, init_jobs
from .helper import get_test_jobs_directory, get_test_examples_directory, prepare_test_output_directory, get_test_example_file, get_test_output_file


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


def test_job_create() -> None:
	commands = [ sys.executable, 'run.py', '--job-create', 'test-job-create' ]
	run = subprocess.run(commands)

	assert run.returncode == 0


@pytest.mark.skip()
def test_job_create_invalid() -> None:
	pass


@pytest.mark.skip()
def test_job_delete() -> None:
	pass


@pytest.mark.skip()
def test_job_delete_invalid() -> None:
	pass


@pytest.mark.skip()
def test_job_add_step() -> None:
	pass


@pytest.mark.skip()
def test_job_add_step_invalid() -> None:
	pass


@pytest.mark.skip()
def test_job_remix() -> None:
	pass


@pytest.mark.skip()
def test_job_remix_invalid() -> None:
	pass


@pytest.mark.skip()
def test_job_insert_step() -> None:
	pass


@pytest.mark.skip()
def test_job_insert_step_invalid() -> None:
	pass


@pytest.mark.skip()
def test_job_remove_step() -> None:
	pass


@pytest.mark.skip()
def test_job_run() -> None:
	pass


@pytest.mark.skip()
def test_job_run_invalid() -> None:
	pass


@pytest.mark.skip()
def test_job_run_all() -> None:
	pass


@pytest.mark.skip()
def test_job_run_all_invalid() -> None:
	pass
