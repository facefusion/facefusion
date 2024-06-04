import json
import subprocess
import shutil
import pytest
import facefusion.core

from argparse import Namespace
from facefusion.download import conditional_download
from facefusion.job_manager import init_jobs, clear_jobs, get_job_status
from facefusion.job_runner import run_job


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	clear_jobs('.jobs')
	init_jobs('.jobs')
	conditional_download('.assets/examples',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vframes', '1', '.assets/examples/target-240p.jpg' ])


def copy_json(source_path : str, destination_path : str) -> None:
	shutil.copyfile(source_path, destination_path)


def prepare_default_args() -> Namespace:
	with open('tests/providers/default_args.json', 'r') as json_file:
		default_args = json.load(json_file)
	return Namespace(**default_args)


def test_run_job() -> None:
	default_args = prepare_default_args()
	handle_step = lambda step_args: (facefusion.core.handle_step(default_args, step_args))

	copy_json('tests/providers/test_run_job.json', './.jobs/queued/test_run_job.json')
	assert run_job('test_run_job', handle_step)
	assert get_job_status('test_run_job') == 'completed'


def test_run_job_merge_action() -> None:
	default_args = prepare_default_args()
	handle_step = lambda step_args: (facefusion.core.handle_step(default_args, step_args))

	copy_json('tests/providers/test_run_job_merge_action.json', './.jobs/queued/test_run_job_merge_action.json')
	assert run_job('test_run_job_merge_action', handle_step)
	assert get_job_status('test_run_job_merge_action') == 'completed'


def test_run_job_remix_action() -> None:
	default_args = prepare_default_args()
	handle_step = lambda step_args: (facefusion.core.handle_step(default_args, step_args))

	copy_json('tests/providers/test_run_job_remix_action.json', './.jobs/queued/test_run_job_remix_action.json')
	assert run_job('test_run_job_remix_action', handle_step)
	assert get_job_status('test_run_job_remix_action') == 'completed'
