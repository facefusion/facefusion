import pytest


from facefusion.job_manager import init_jobs, clear_jobs, create_job, delete_job, find_job_ids, move_job_file, add_step, remix_step, insert_step, remove_step, get_steps, set_step_status
from .helper import get_test_jobs_directory


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(get_test_jobs_directory())


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
	args_1 =\
	{
		'source_path': 'source-1.jpg',
		'target_path': 'target-1.jpg',
		'output_path': 'output-1.jpg'
	}
	args_2 =\
	{
		'source_path': 'source-2.jpg',
		'target_path': 'target-2.jpg',
		'output_path': 'output-2.jpg'
	}

	assert add_step('job-test-add-step', args_1) is False

	create_job('job-test-add-step')

	assert add_step('job-test-add-step', args_1) is True
	assert add_step('job-test-add-step', args_2) is True

	steps = get_steps('job-test-add-step')

	assert steps[0].get('args') == args_1
	assert steps[1].get('args') == args_2


def test_remix_step() -> None:
	args_1 =\
	{
		'source_path': 'source-1.jpg',
		'target_path': 'target-1.jpg',
		'output_path': 'output-1.jpg'
	}
	args_2 =\
	{
		'source_path': 'source-2.jpg',
		'target_path': 'target-2.jpg',
		'output_path': 'output-2.jpg'
	}

	assert remix_step('job-test-remix-step', 0, args_1) is False

	create_job('job-test-remix-step')
	add_step('job-test-remix-step', args_1)
	add_step('job-test-remix-step', args_2)

	assert remix_step('job-test-remix-step', 0, args_2) is True

	steps = get_steps('job-test-remix-step')

	assert steps[0].get('args') == args_1
	assert steps[1].get('args') == args_2
	assert steps[2].get('args').get('source_path') == args_2.get('source_path')
	assert steps[2].get('args').get('target_path') == args_1.get('output_path')
	assert steps[2].get('args').get('output_path') == args_2.get('output_path')


def test_insert_step() -> None:
	args_1 =\
	{
		'source_path': 'source-1.jpg',
		'target_path': 'target-1.jpg',
		'output_path': 'output-1.jpg'
	}
	args_2 =\
	{
		'source_path': 'source-2.jpg',
		'target_path': 'target-2.jpg',
		'output_path': 'output-2.jpg'
	}

	assert insert_step('job-test-insert-step', 0, args_1) is False

	create_job('job-test-insert-step')
	add_step('job-test-insert-step', args_1)
	add_step('job-test-insert-step', args_1)

	assert insert_step('job-test-insert-step', 1, args_2) is True

	steps = get_steps('job-test-insert-step')

	assert steps[0].get('args') == args_1
	assert steps[1].get('args') == args_2
	assert steps[2].get('args') == args_1


def test_remove_step() -> None:
	args_1 =\
	{
		'source_path': 'source-1.jpg',
		'target_path': 'target-1.jpg',
		'output_path': 'output-1.jpg'
	}
	args_2 =\
	{
		'source_path': 'source-2.jpg',
		'target_path': 'target-2.jpg',
		'output_path': 'output-2.jpg'
	}

	assert remove_step('job-test-insert-step', 0) is False

	create_job('job-test-remove-step')
	add_step('job-test-remove-step', args_1)
	add_step('job-test-remove-step', args_2)
	add_step('job-test-remove-step', args_1)

	assert remove_step('job-test-remove-step', 1) is True

	steps = get_steps('job-test-remove-step')

	assert steps[0].get('args') == args_1
	assert steps[1].get('args') == args_1


def test_get_steps() -> None:
	args_1 =\
	{
		'source_path': 'source-1.jpg',
		'target_path': 'target-1.jpg',
		'output_path': 'output-1.jpg'
	}
	args_2 =\
	{
		'source_path': 'source-2.jpg',
		'target_path': 'target-2.jpg',
		'output_path': 'output-2.jpg'
	}

	assert get_steps('job-test-get-steps') == []

	create_job('job-test-get-steps')
	add_step('job-test-get-steps', args_1)
	add_step('job-test-get-steps', args_2)
	steps = get_steps('job-test-get-steps')

	assert steps[0].get('args') == args_1
	assert steps[1].get('args') == args_2


def test_set_step_status() -> None:
	args_1 =\
	{
		'source_path': 'source-1.jpg',
		'target_path': 'target-1.jpg',
		'output_path': 'output-1.jpg'
	}
	args_2 =\
	{
		'source_path': 'source-2.jpg',
		'target_path': 'target-2.jpg',
		'output_path': 'output-2.jpg'
	}

	assert set_step_status('job-test-set-step-status', 0, 'completed') is False

	create_job('job-test-set-step-status')
	add_step('job-test-set-step-status', args_1)
	add_step('job-test-set-step-status', args_2)

	assert set_step_status('job-test-set-step-status', 0, 'completed') is True
	assert set_step_status('job-test-set-step-status', 1, 'failed') is True

	steps = get_steps('job-test-set-step-status')

	assert steps[0].get('status') == 'completed'
	assert steps[1].get('status') == 'failed'
