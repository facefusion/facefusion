import subprocess

import pytest

from facefusion.download import conditional_download
from facefusion.filesystem import copy_file
from facefusion.jobs.job_manager import add_step, clear_jobs, create_job, init_jobs, move_job_file, submit_job, submit_jobs
from facefusion.jobs.job_runner import collect_output_set, finalize_steps, retry_job, retry_jobs, run_job, run_jobs, run_steps
from facefusion.types import Args
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


def process_step(job_id : str, step_index : int, step_args : Args) -> bool:
	return copy_file(step_args.get('target_path'), step_args.get('output_path'))


def test_run_job() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_file('output-1.mp4')
	}
	args_2 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_file('output-2.mp4')
	}
	args_3 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_file('output-3.jpg')
	}

	assert run_job('job-invalid', process_step) is False

	create_job('job-test-run-job')
	add_step('job-test-run-job', args_1)
	add_step('job-test-run-job', args_2)
	add_step('job-test-run-job', args_2)
	add_step('job-test-run-job', args_3)

	assert run_job('job-test-run-job', process_step) is False

	submit_job('job-test-run-job')

	assert run_job('job-test-run-job', process_step) is True


def test_run_jobs() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_file('output-1.mp4')
	}
	args_2 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_file('output-2.mp4')
	}
	args_3 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_file('output-3.jpg')
	}
	halt_on_error = True

	assert run_jobs(process_step, halt_on_error) is False

	create_job('job-test-run-jobs-1')
	create_job('job-test-run-jobs-2')
	add_step('job-test-run-jobs-1', args_1)
	add_step('job-test-run-jobs-1', args_1)
	add_step('job-test-run-jobs-2', args_2)
	add_step('job-test-run-jobs-3', args_3)

	assert run_jobs(process_step, halt_on_error) is False

	submit_jobs(halt_on_error)

	assert run_jobs(process_step, halt_on_error) is True


def test_retry_job() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_file('output-1.mp4')
	}

	assert retry_job('job-invalid', process_step) is False

	create_job('job-test-retry-job')
	add_step('job-test-retry-job', args_1)
	submit_job('job-test-retry-job')

	assert retry_job('job-test-retry-job', process_step) is False

	move_job_file('job-test-retry-job', 'failed')

	assert retry_job('job-test-retry-job', process_step) is True


def test_retry_jobs() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_file('output-1.mp4')
	}
	args_2 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_file('output-2.mp4')
	}
	args_3 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_file('output-3.jpg')
	}
	halt_on_error = True

	assert retry_jobs(process_step, halt_on_error) is False

	create_job('job-test-retry-jobs-1')
	create_job('job-test-retry-jobs-2')
	add_step('job-test-retry-jobs-1', args_1)
	add_step('job-test-retry-jobs-1', args_1)
	add_step('job-test-retry-jobs-2', args_2)
	add_step('job-test-retry-jobs-3', args_3)

	assert retry_jobs(process_step, halt_on_error) is False

	move_job_file('job-test-retry-jobs-1', 'failed')
	move_job_file('job-test-retry-jobs-2', 'failed')

	assert retry_jobs(process_step, halt_on_error) is True


def test_run_steps() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_file('output-1.mp4')
	}
	args_2 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_file('output-2.mp4')
	}
	args_3 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_file('output-3.jpg')
	}

	assert run_steps('job-invalid', process_step) is False

	create_job('job-test-run-steps')
	add_step('job-test-run-steps', args_1)
	add_step('job-test-run-steps', args_1)
	add_step('job-test-run-steps', args_2)
	add_step('job-test-run-steps', args_3)

	assert run_steps('job-test-run-steps', process_step) is True


def test_finalize_steps() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_file('output-1.mp4')
	}
	args_2 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_file('output-2.mp4')
	}
	args_3 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_file('output-3.jpg')
	}

	create_job('job-test-finalize-steps')
	add_step('job-test-finalize-steps', args_1)
	add_step('job-test-finalize-steps', args_1)
	add_step('job-test-finalize-steps', args_2)
	add_step('job-test-finalize-steps', args_3)

	copy_file(args_1.get('target_path'), get_test_output_file('output-1-job-test-finalize-steps-0.mp4'))
	copy_file(args_1.get('target_path'), get_test_output_file('output-1-job-test-finalize-steps-1.mp4'))
	copy_file(args_2.get('target_path'), get_test_output_file('output-2-job-test-finalize-steps-2.mp4'))
	copy_file(args_3.get('target_path'), get_test_output_file('output-3-job-test-finalize-steps-3.jpg'))

	assert finalize_steps('job-test-finalize-steps') is True
	assert is_test_output_file('output-1.mp4') is True
	assert is_test_output_file('output-2.mp4') is True
	assert is_test_output_file('output-3.jpg') is True


def test_collect_output_set() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_file('output-1.mp4')
	}
	args_2 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_file('output-2.mp4')
	}
	args_3 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_file('output-3.jpg')
	}

	create_job('job-test-collect-output-set')
	add_step('job-test-collect-output-set', args_1)
	add_step('job-test-collect-output-set', args_1)
	add_step('job-test-collect-output-set', args_2)
	add_step('job-test-collect-output-set', args_3)

	output_set =\
	{
		get_test_output_file('output-1.mp4'):
		[
			get_test_output_file('output-1-job-test-collect-output-set-0.mp4'),
			get_test_output_file('output-1-job-test-collect-output-set-1.mp4')
		],
		get_test_output_file('output-2.mp4'):
		[
			get_test_output_file('output-2-job-test-collect-output-set-2.mp4')
		],
		get_test_output_file('output-3.jpg'):
		[
			get_test_output_file('output-3-job-test-collect-output-set-3.jpg')
		]
	}

	assert collect_output_set('job-test-collect-output-set') == output_set
