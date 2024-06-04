import subprocess
import sys
import pytest

from typing import Any
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


def run_command(commands : list[str]) -> Any:
	return subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)


@pytest.mark.skip() # TODO : Fix
def test_job() -> None:
	commands = [ sys.executable, 'run.py', '--job-create', 'job0' ]
	run = run_command(commands)
	assert run.returncode == 0
	assert 'Job created' in run.stdout.decode()

	run = run_command(commands)
	assert run.returncode == 0
	assert 'Job not created' in run.stdout.decode()

	commands = [ sys.executable, 'run.py', '--frame-processors', 'face_swapper', '-s', '.assets/examples/source.jpg', '-t', '.assets/examples/target-240p.jpg', '-o', '.assets/examples/test_cli_jobs.jpg', '--job-add-step', 'job0' ]
	run = run_command(commands)
	assert run.returncode == 0
	assert 'Job step added' in run.stdout.decode()

	commands = [ sys.executable, 'run.py', '--job-add-step', 'invalid' ]
	run = run_command(commands)
	assert run.returncode == 0
	assert 'Job step not added' in run.stdout.decode()

	commands = [ sys.executable, 'run.py', '--job-insert-step', 'job0', '-1' ]
	run = run_command(commands)
	assert run.returncode == 0
	assert 'Job step inserted' in run.stdout.decode()

	commands = [ sys.executable, 'run.py', '--job-remove-step', 'job0', '-1' ]
	run = run_command(commands)
	assert run.returncode == 0
	assert 'Job step removed' in run.stdout.decode()

	commands = [ sys.executable, 'run.py', '--job-run', 'job0' ]
	run = run_command(commands)
	assert run.returncode == 0
	assert '1 of 1 steps processed in job0' in run.stdout.decode()
