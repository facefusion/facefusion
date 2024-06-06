import pytest

from facefusion.job_manager import init_jobs, clear_jobs, create_job, delete_job, find_job_ids, move_job_file, add_step, get_steps


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs('.jobs')
	init_jobs('.jobs')


def test_create_job() -> None:
	assert create_job('job-test-create-job') is True
	assert create_job('job-test-create-job') is False


def test_delete_job() -> None:
	assert delete_job('job-test-delete-job') is False

	create_job('job-test-delete-job')

	assert delete_job('job-test-delete-job') is True
	assert delete_job('job-test-delete-job') is False


def test_find_job_ids() -> None:
	create_job('job-test-find-job-ids-1')
	create_job('job-test-find-job-ids-2')
	create_job('job-test-find-job-ids-3')

	assert find_job_ids('queued') == [ 'job-test-find-job-ids-1', 'job-test-find-job-ids-2', 'job-test-find-job-ids-3' ]
	assert find_job_ids('completed') == []
	assert find_job_ids('failed') == []

	move_job_file('job-test-find-job-ids-1', 'completed')

	assert find_job_ids('queued') == [ 'job-test-find-job-ids-2', 'job-test-find-job-ids-3' ]
	assert find_job_ids('completed') == [ 'job-test-find-job-ids-1' ]
	assert find_job_ids('failed') == []

	move_job_file('job-test-find-job-ids-2', 'failed')

	assert find_job_ids('queued') == [ 'job-test-find-job-ids-3' ]
	assert find_job_ids('completed') == [ 'job-test-find-job-ids-1' ]
	assert find_job_ids('failed') == [ 'job-test-find-job-ids-2' ]

	move_job_file('job-test-find-job-ids-3', 'completed')

	assert find_job_ids('queued') == [ ]
	assert find_job_ids('completed') == [ 'job-test-find-job-ids-1', 'job-test-find-job-ids-3' ]
	assert find_job_ids('failed') == [ 'job-test-find-job-ids-2' ]


def test_add_step() -> None:
	step_args_1 =\
	{
		'source': '.assets/examples/source-1.jpg'
	}
	step_args_2 =\
	{
		'source': '.assets/examples/source-2.jpg'
	}
	step_args_3 = \
	{
		'source': '.assets/examples/source-3.jpg'
	}

	assert add_step('job-test-add-step', step_args_1) is False

	create_job('job-test-add-step')

	assert add_step('job-test-add-step', step_args_1) is True
	assert add_step('job-test-add-step', step_args_2) is True
	assert add_step('job-test-add-step', step_args_2) is True
	assert add_step('job-test-add-step', step_args_3) is True

	steps = get_steps('job-test-add-step')

	for index, step_args in enumerate([ step_args_1, step_args_2, step_args_2, step_args_3 ]):
		assert steps[index].get('args') == step_args


@pytest.mark.skip()
def test_remix_step() -> None:
	pass


@pytest.mark.skip()
def test_insert_step() -> None:
	pass


@pytest.mark.skip()
def test_remove_step() -> None:
	pass


@pytest.mark.skip()
def test_get_steps() -> None:
	pass


@pytest.mark.skip()
def test_set_step_status() -> None:
	pass
