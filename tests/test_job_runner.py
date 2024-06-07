import pytest

from facefusion.typing import Args
from facefusion.job_manager import init_jobs, clear_jobs, create_job, add_step
from facefusion.job_runner import run_job, run_jobs
from .helper import get_test_jobs_directory


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
		'source_path': '.assets/examples/source-1.jpg',
		'target_path': '.assets/examples/target-1.jpg',
		'output_path': '.assets/examples/output-1.jpg'
	}
	args_2 =\
	{
		'source_path': '.assets/examples/source-2.jpg',
		'target_path': '.assets/examples/target-2.jpg',
		'output_path': '.assets/examples/output-1.jpg'
	}
	args_3 =\
	{
		'source_path': '.assets/examples/source-3.jpg',
		'target_path': '.assets/examples/target-3.jpg',
		'output_path': '.assets/examples/output-3.jpg'
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
		'source_path': '.assets/examples/source-1.jpg',
		'target_path': '.assets/examples/target-1.jpg',
		'output_path': '.assets/examples/output-1.jpg'
	}
	args_2 =\
	{
		'source_path': '.assets/examples/source-2.jpg',
		'target_path': '.assets/examples/target-2.jpg',
		'output_path': '.assets/examples/output-1.jpg'
	}
	args_3 =\
	{
		'source_path': '.assets/examples/source-3.jpg',
		'target_path': '.assets/examples/target-3.jpg',
		'output_path': '.assets/examples/output-3.jpg'
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


@pytest.mark.skip()
def test_collect_merge_set() -> None:
	pass
