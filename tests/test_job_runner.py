import os
import subprocess
import tempfile

import pytest

from facefusion.typing import Args
from facefusion.download import conditional_download
from facefusion.job_manager import init_jobs, clear_jobs, create_job, add_step
from facefusion.job_runner import run_job, run_jobs, collect_merge_set
from .helper import get_test_jobs_directory, get_test_examples_directory, get_test_example_file, get_test_output_file


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-1080p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vframes', '1', get_test_example_file('target-240p.jpg') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-1080p.mp4'), '-vframes', '1', get_test_example_file('target-1080p.jpg') ])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(get_test_jobs_directory())


def process_step(step_args : Args) -> bool:
	return 'source_path' in step_args and 'target_path' in step_args and 'output_path' in step_args


@pytest.mark.skip()
def test_run_jobs() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_example_file('output.mp4')
	}
	args_2 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_example_file('output.mp4')
	}
	args_3 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_example_file('output.jpg')
	}

	assert run_jobs(process_step) is False

	create_job('job-test-run-job')
	add_step('job-test-run-job', args_1)
	add_step('job-test-run-job', args_2)
	add_step('job-test-run-job', args_3)

	assert run_job('job-test-run-job', process_step) is True


@pytest.mark.skip()
def test_run_all_job() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_example_file('output.mp4')
	}
	args_2 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_example_file('output.mp4')
	}
	args_3 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_example_file('output.jpg')
	}

	assert run_jobs(process_step) is False

	create_job('job-test-run-jobs-1')
	create_job('job-test-run-jobs-2')
	add_step('job-test-run-jobs-1', args_1)
	add_step('job-test-run-jobs-1', args_2)
	add_step('job-test-run-jobs-2', args_3)

	assert run_jobs(process_step) is True


@pytest.mark.skip()
def test_run_steps() -> None:
	pass


@pytest.mark.skip()
def test_finalize_steps() -> None:
	pass


def test_collect_merge_set() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_example_file('output.mp4')
	}
	args_2 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_example_file('output.mp4')
	}
	args_3 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_example_file('output.jpg')
	}
	args_4 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-1080p.jpg'),
		'output_path': get_test_example_file('output')
	}

	create_job('job-collect-merge-set')
	add_step('job-collect-merge-set', args_1)
	add_step('job-collect-merge-set', args_2)
	add_step('job-collect-merge-set', args_3)
	add_step('job-collect-merge-set', args_4)

	merge_set =\
	{
		get_test_example_file('output.mp4'):
		[
			os.path.join(tempfile.gettempdir(), 'test-examples', 'output-job-collect-merge-set-0.mp4'),
			os.path.join(tempfile.gettempdir(), 'test-examples', 'output-job-collect-merge-set-1.mp4')
		],
		get_test_example_file('output.jpg'):
		[
			os.path.join(tempfile.gettempdir(), 'test-examples', 'output-job-collect-merge-set-2.jpg')
		],
		os.path.join(get_test_examples_directory(), 'output'):
		[
			os.path.join(get_test_examples_directory(), 'output-job-collect-merge-set-3')
		]
	}

	assert collect_merge_set('job-collect-merge-set') == merge_set
