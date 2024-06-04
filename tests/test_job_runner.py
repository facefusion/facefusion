import subprocess
import shutil
import pytest
import facefusion.core

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


def test_run_job() -> None:
	shutil.copyfile('tests/providers/test_run_job.json', '.jobs/queued/test_run_job.json')

	assert run_job('test_run_job', facefusion.core.handle_step)
	assert get_job_status('test_run_job') == 'completed'


@pytest.mark.skip()
def test_run_job_with_merge() -> None:
	shutil.copyfile('tests/providers/test_run_job_merge.json', '.jobs/queued/test_run_job_merge.json')

	assert run_job('test_run_job_merge_action', facefusion.core.handle_step)
	assert get_job_status('test_run_job_merge_action') == 'completed'


@pytest.mark.skip()
def test_run_job_with_remix() -> None:
	shutil.copyfile('tests/providers/test_run_job_remix.json', '.jobs/queued/test_run_job_remix.json')

	assert run_job('test_run_job_remix_action', facefusion.core.handle_step)
	assert get_job_status('test_run_job_remix_action') == 'completed'
