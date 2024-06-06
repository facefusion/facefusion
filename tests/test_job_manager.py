import pytest

from facefusion.job_manager import init_jobs, clear_jobs, create_job, delete_job, find_job_ids, move_job_file, add_step, remix_step, get_steps


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
	add_args_1 =\
	{
		'source_path': '.assets/examples/source-1.jpg',
		'target_path': '.assets/examples/target-1.jpg',
		'output_path': '.assets/examples/output-1.jpg'
	}
	add_args_2 =\
	{
		'source_path': '.assets/examples/source-2.jpg',
		'target_path': '.assets/examples/target-2.jpg',
		'output_path': '.assets/examples/output-2.jpg'
	}

	assert add_step('job-test-add-step', add_args_1) is False

	create_job('job-test-add-step')

	assert add_step('job-test-add-step', add_args_1) is True
	assert add_step('job-test-add-step', add_args_2) is True

	steps = get_steps('job-test-add-step')

	assert steps[0].get('args') == add_args_1
	assert steps[1].get('args') == add_args_2


def test_remix_step() -> None:
	add_args_1 =\
	{
		'source_path': '.assets/examples/source-1.jpg',
		'target_path': '.assets/examples/target-1.jpg',
		'output_path': '.assets/examples/output-1.jpg'
	}
	add_args_2 =\
	{
		'source_path': '.assets/examples/source-2.jpg',
		'target_path': '.assets/examples/target-2.jpg',
		'output_path': '.assets/examples'
	}

	assert remix_step('job-test-remix-step', 0, add_args_1) is False

	create_job('job-test-remix-step')

	assert add_step('job-test-remix-step', add_args_1) is True
	assert add_step('job-test-remix-step', add_args_2) is True
	assert remix_step('job-test-remix-step', 0, add_args_1) is True
	assert remix_step('job-test-remix-step', 1, add_args_2) is True

	steps = get_steps('job-test-remix-step')

	assert steps[0].get('args') == add_args_1
	assert steps[1].get('args') == add_args_2
	assert steps[2].get('args').get('source_path') == add_args_1.get('source_path')
	assert steps[2].get('args').get('target_path') == add_args_1.get('output_path')
	assert steps[2].get('args').get('output_path') == add_args_1.get('output_path')
	assert steps[3].get('args').get('source_path') == add_args_2.get('source_path')
	assert steps[3].get('args').get('target_path') == '.assets/examples/target-2-caf648bd.jpg'
	assert steps[3].get('args').get('output_path') == add_args_2.get('output_path')


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
