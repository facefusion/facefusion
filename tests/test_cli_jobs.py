import subprocess
import sys
import pytest

from facefusion.download import conditional_download
from facefusion.job_manager import clear_jobs


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	clear_jobs('.jobs')
	conditional_download('.assets/examples',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vframes', '1', '.assets/examples/target-240p.jpg' ])


def test_job_create() -> None:
	commands = [ sys.executable, 'run.py', '--job-create', 'job-one' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert 'Job created' in run.stdout.decode()


def test_job_create_invalid() -> None:
	commands = [ sys.executable, 'run.py', '--job-create', 'job-one' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	# assert run.returncode == 1 # todo: error code should be 1
	assert 'Job not created' in run.stdout.decode()


@pytest.mark.skip()
def test_job_delete() -> None:
	pass


@pytest.mark.skip()
def test_job_delete_invalid() -> None:
	pass


def test_job_add_step() -> None:
	commands = [ sys.executable, 'run.py', '--job-add-step', 'job-one', '-s', '.assets/examples/source.jpg', '-t', '.assets/examples/target-240p.jpg', '-o', '.' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert 'Job step added' in run.stdout.decode()


def test_job_add_step_invalid() -> None:
	commands = [ sys.executable, 'run.py', '--job-add-step', 'job-invalid' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	#assert run.returncode == 1 # todo: error code should be 1
	assert 'Job step not added' in run.stdout.decode()


@pytest.mark.skip()
def test_job_remix() -> None:
	pass


@pytest.mark.skip()
def test_job_remix_invalid() -> None:
	pass


def test_job_insert_step() -> None:
	commands = [ sys.executable, 'run.py', '--job-insert-step', 'job-one', '-1', '-s', '.assets/examples/source.jpg', '-t', '.assets/examples/target-240p.jpg', '-o', '.' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert 'Job step inserted' in run.stdout.decode()


@pytest.mark.skip()
def test_job_insert_step_invalid() -> None:
	commands = [ sys.executable, 'run.py', '--job-insert-step', 'job-invalid', '-1' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 1
	assert 'Job step not inserted' in run.stdout.decode()


@pytest.mark.skip()
def test_job_remove_step() -> None:
	commands = [ sys.executable, 'run.py', '--job-remove-step', 'job-one', '-1' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert 'Job step removed' in run.stdout.decode()


@pytest.mark.skip()
def test_job_run() -> None:
	commands = [ sys.executable, 'run.py', '--job-run', 'job-one' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert '1 of 1 steps processed in job-one' in run.stdout.decode()


@pytest.mark.skip()
def test_job_run_invalid() -> None:
	pass


@pytest.mark.skip()
def test_job_run_all() -> None:
	pass


@pytest.mark.skip()
def test_job_run_all_invalid() -> None:
	pass
