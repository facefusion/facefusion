import hashlib
import os
from time import sleep

import pytest

from facefusion import state_manager
from facefusion.filesystem import create_directory, is_directory
from facefusion.jobs.job_helper import get_step_output_path
from facefusion.jobs.job_manager import add_step, clear_jobs, count_step_total, create_job, delete_job, delete_jobs, find_job_ids, find_job_path, find_jobs, get_job_file_name, get_steps, has_step, init_jobs, insert_step, move_job_file, read_job_file, remix_step, remove_step, set_step_status, set_steps_status, submit_job, submit_jobs, suggest_job_path, update_job_file, validate_job
from facefusion.json import write_json
from facefusion.session_context import resolve_local_id, set_session_id
from .assert_helper import get_test_job_file, get_test_jobs_directory, is_test_job_file


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('jobs_path', get_test_jobs_directory())


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	local_id = resolve_local_id()

	set_session_id(local_id)
	clear_jobs(get_test_jobs_directory())
	init_jobs(state_manager.get_jobs_path())


def test_init_jobs() -> None:
	local_id = resolve_local_id()

	set_session_id('session-a')
	state_manager.init()

	assert init_jobs(state_manager.get_jobs_path()) is True
	assert os.path.isdir(os.path.join(get_test_jobs_directory(), 'session-a', 'drafted')) is True

	create_job('job-test-init-jobs')

	assert find_job_ids('drafted') == [ 'job-test-init-jobs' ]

	set_session_id(local_id)

	assert find_job_ids('drafted') == []
	assert is_directory(os.path.join(state_manager.get_jobs_path(), 'drafted')) is True
	assert is_directory(os.path.join(state_manager.get_jobs_path(), 'queued')) is True
	assert is_directory(os.path.join(state_manager.get_jobs_path(), 'failed')) is True
	assert is_directory(os.path.join(state_manager.get_jobs_path(), 'completed')) is True

	clear_jobs(get_test_jobs_directory())
	create_directory(state_manager.get_jobs_path())
	write_json(os.path.join(state_manager.get_jobs_path(), 'completed'), {})

	assert init_jobs(state_manager.get_jobs_path()) is False
	assert is_directory(os.path.join(state_manager.get_jobs_path(), 'drafted')) is True
	assert is_directory(os.path.join(state_manager.get_jobs_path(), 'completed')) is False


def test_clear_jobs() -> None:
	create_job('job-test-clear-jobs')

	assert clear_jobs(get_test_jobs_directory()) is True
	assert is_directory(get_test_jobs_directory()) is False
	assert clear_jobs(get_test_jobs_directory()) is False


def test_create_job() -> None:
	args_1 =\
	{
		'source_path': 'source-1.jpg',
		'target_path': 'target-1.jpg',
		'output_path': 'output-1.jpg'
	}

	assert create_job('job-test-create-job') is True
	assert is_test_job_file('job-test-create-job.json', 'drafted') is True
	assert read_job_file('job-test-create-job').get('version') == '1'
	assert read_job_file('job-test-create-job').get('date_updated') is None
	assert read_job_file('job-test-create-job').get('steps') == []
	assert create_job('job-test-create-job') is False

	add_step('job-test-create-job', args_1)
	submit_job('job-test-create-job')

	assert is_test_job_file('job-test-create-job.json', 'queued') is True
	assert create_job('job-test-create-job') is False
	assert is_test_job_file('job-test-create-job.json', 'drafted') is False


def test_submit_job() -> None:
	args_1 =\
	{
		'source_path': 'source-1.jpg',
		'target_path': 'target-1.jpg',
		'output_path': 'output-1.jpg'
	}
	args_2 =\
	{
		'source_path': 'source-2.jpg',
		'target_path': 'target-2.mp4',
		'output_path': 'output-sequence-2'
	}

	assert submit_job('job-invalid') is False

	create_job('job-test-submit-job')

	assert submit_job('job-test-submit-job') is False

	add_step('job-test-submit-job', args_1)
	add_step('job-test-submit-job', args_2)

	assert submit_job('job-test-submit-job') is True
	assert is_test_job_file('job-test-submit-job.json', 'drafted') is False
	assert is_test_job_file('job-test-submit-job.json', 'queued') is True
	assert get_steps('job-test-submit-job')[0].get('status') == 'queued'
	assert get_steps('job-test-submit-job')[1].get('status') == 'queued'
	assert submit_job('job-test-submit-job') is False

	move_job_file('job-test-submit-job', 'failed')

	assert submit_job('job-test-submit-job') is False
	assert is_test_job_file('job-test-submit-job.json', 'failed') is True


def test_submit_jobs() -> None:
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
	halt_on_error = True

	assert submit_jobs(halt_on_error) is False

	create_job('job-test-submit-jobs-1')
	create_job('job-test-submit-jobs-2')

	assert submit_jobs(halt_on_error) is False

	add_step('job-test-submit-jobs-1', args_1)
	add_step('job-test-submit-jobs-2', args_2)

	assert submit_jobs(halt_on_error) is True
	assert find_job_ids('queued') == [ 'job-test-submit-jobs-1', 'job-test-submit-jobs-2' ]
	assert submit_jobs(halt_on_error) is False

	create_job('job-test-submit-jobs-3')
	sleep(0.5)
	create_job('job-test-submit-jobs-4')
	add_step('job-test-submit-jobs-4', args_2)

	assert submit_jobs(halt_on_error) is False
	assert find_job_ids('drafted') == [ 'job-test-submit-jobs-3', 'job-test-submit-jobs-4' ]

	halt_on_error = False

	assert submit_jobs(halt_on_error) is False
	assert find_job_ids('drafted') == [ 'job-test-submit-jobs-3' ]
	assert is_test_job_file('job-test-submit-jobs-4.json', 'queued') is True


def test_delete_job() -> None:
	assert delete_job('job-invalid') is False

	create_job('job-test-delete-job')

	assert delete_job('job-test-delete-job') is True
	assert is_test_job_file('job-test-delete-job.json', 'drafted') is False
	assert delete_job('job-test-delete-job') is False


def test_delete_jobs() -> None:
	halt_on_error = True

	assert delete_jobs(halt_on_error) is False

	create_job('job-test-delete-jobs-1')
	create_job('job-test-delete-jobs-2')
	create_job('job-test-delete-jobs-3')
	create_job('job-test-delete-jobs-4')
	move_job_file('job-test-delete-jobs-2', 'queued')
	move_job_file('job-test-delete-jobs-3', 'failed')
	move_job_file('job-test-delete-jobs-4', 'completed')

	assert delete_jobs(halt_on_error) is True
	assert find_job_ids('drafted') == []
	assert find_job_ids('queued') == []
	assert find_job_ids('failed') == []
	assert find_job_ids('completed') == []
	assert delete_jobs(halt_on_error) is False

	create_directory(get_test_job_file('job-test-delete-jobs-5.json', 'drafted'))
	sleep(0.5)
	create_job('job-test-delete-jobs-6')

	assert delete_jobs(halt_on_error) is False
	assert find_job_ids('drafted') == [ 'job-test-delete-jobs-5', 'job-test-delete-jobs-6' ]

	halt_on_error = False

	assert delete_jobs(halt_on_error) is False
	assert find_job_ids('drafted') == [ 'job-test-delete-jobs-5' ]


def test_find_jobs() -> None:
	create_job('job-test-find-jobs-1')
	sleep(0.5)
	create_job('job-test-find-jobs-2')

	assert list(find_jobs('drafted').keys()) == [ 'job-test-find-jobs-1', 'job-test-find-jobs-2' ]
	assert find_jobs('drafted').get('job-test-find-jobs-1') == read_job_file('job-test-find-jobs-1')
	assert find_jobs('queued') == {}

	move_job_file('job-test-find-jobs-1', 'queued')

	assert 'job-test-find-jobs-2' in find_jobs('drafted')
	assert 'job-test-find-jobs-1' in find_jobs('queued')


def test_find_job_ids() -> None:
	create_job('job-test-find-job-ids-1')
	sleep(0.5)
	create_job('job-test-find-job-ids-2')
	sleep(0.5)
	create_job('job-test-find-job-ids-3')

	assert find_job_ids('drafted') == [ 'job-test-find-job-ids-1', 'job-test-find-job-ids-2', 'job-test-find-job-ids-3' ]
	assert find_job_ids('queued') == []
	assert find_job_ids('completed') == []
	assert find_job_ids('failed') == []

	move_job_file('job-test-find-job-ids-1', 'queued')
	move_job_file('job-test-find-job-ids-2', 'queued')
	move_job_file('job-test-find-job-ids-3', 'queued')

	assert find_job_ids('drafted') == []
	assert find_job_ids('queued') == [ 'job-test-find-job-ids-1', 'job-test-find-job-ids-2', 'job-test-find-job-ids-3' ]
	assert find_job_ids('completed') == []
	assert find_job_ids('failed') == []

	move_job_file('job-test-find-job-ids-1', 'completed')

	assert find_job_ids('drafted') == []
	assert find_job_ids('queued') == [ 'job-test-find-job-ids-2', 'job-test-find-job-ids-3' ]
	assert find_job_ids('completed') == [ 'job-test-find-job-ids-1' ]
	assert find_job_ids('failed') == []

	move_job_file('job-test-find-job-ids-2', 'failed')

	assert find_job_ids('drafted') == []
	assert find_job_ids('queued') == [ 'job-test-find-job-ids-3' ]
	assert find_job_ids('completed') == [ 'job-test-find-job-ids-1' ]
	assert find_job_ids('failed') == [ 'job-test-find-job-ids-2' ]

	move_job_file('job-test-find-job-ids-3', 'completed')

	assert find_job_ids('drafted') == []
	assert find_job_ids('queued') == []
	assert find_job_ids('completed') == [ 'job-test-find-job-ids-1', 'job-test-find-job-ids-3' ]
	assert find_job_ids('failed') == [ 'job-test-find-job-ids-2' ]


def test_validate_job() -> None:
	assert validate_job('job-invalid') is False

	create_job('job-test-validate-job-1')

	assert validate_job('job-test-validate-job-1') is True

	write_json(get_test_job_file('job-test-validate-job-2.json', 'drafted'),
	{
		'version': '1',
		'date_created': None,
		'steps': []
	})

	assert validate_job('job-test-validate-job-2') is False


def test_has_step() -> None:
	args_1 =\
	{
		'source_path': 'source-1.jpg',
		'target_path': 'target-1.jpg',
		'output_path': 'output-1.jpg'
	}

	assert has_step('job-invalid', 0) is False

	create_job('job-test-has-step')

	assert has_step('job-test-has-step', 0) is False

	add_step('job-test-has-step', args_1)
	add_step('job-test-has-step', args_1)

	assert has_step('job-test-has-step', 0) is True
	assert has_step('job-test-has-step', 1) is True
	assert has_step('job-test-has-step', 2) is False
	assert has_step('job-test-has-step', -1) is False


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
	args_3 =\
	{
		'source_path': 'source-3.jpg',
		'target_path': 'target-3.mp4',
		'output_path': 'output-sequence-1'
	}
	args_4 =\
	{
		'source_path': 'source-4.jpg',
		'target_path': 'target-4.mp4',
		'output_path': 'output-sequence-1'
	}

	assert add_step('job-invalid', args_1) is False

	create_job('job-test-add-step')

	assert add_step('job-test-add-step', args_1) is True
	assert add_step('job-test-add-step', args_2) is True
	assert add_step('job-test-add-step', args_3) is True
	assert add_step('job-test-add-step', args_4) is True

	steps = get_steps('job-test-add-step')

	assert steps[0].get('args') == args_1
	assert steps[1].get('args') == args_2
	assert steps[2].get('args') == args_3
	assert steps[3].get('args') == args_4
	assert steps[0].get('status') == 'drafted'
	assert steps[3].get('status') == 'drafted'
	assert count_step_total('job-test-add-step') == 4


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
	args_3 =\
	{
		'source_path': 'source-3.jpg',
		'target_path': 'target-3.mp4',
		'output_path': 'output-sequence-3'
	}

	assert remix_step('job-invalid', 0, args_1) is False

	create_job('job-test-remix-step')
	add_step('job-test-remix-step', args_1)
	add_step('job-test-remix-step', args_2)
	add_step('job-test-remix-step', args_3)

	assert remix_step('job-test-remix-step', 99, args_1) is False
	assert remix_step('job-test-remix-step', 0, args_2) is True
	assert remix_step('job-test-remix-step', -1, args_2) is True
	assert remix_step('job-test-remix-step', 2, args_3) is True

	steps = get_steps('job-test-remix-step')

	assert steps[0].get('args') == args_1
	assert steps[1].get('args') == args_2
	assert steps[2].get('args') == args_3
	assert steps[3].get('args').get('source_path') == args_2.get('source_path')
	assert steps[3].get('args').get('target_path') == get_step_output_path('job-test-remix-step', 0, args_1.get('output_path'))
	assert steps[3].get('args').get('output_path') == args_2.get('output_path')
	assert steps[4].get('args').get('source_path') == args_2.get('source_path')
	assert steps[4].get('args').get('target_path') == get_step_output_path('job-test-remix-step', 3, args_2.get('output_path'))
	assert steps[4].get('args').get('output_path') == args_2.get('output_path')
	assert steps[5].get('args').get('source_path') == args_3.get('source_path')
	assert steps[5].get('args').get('target_path') == get_step_output_path('job-test-remix-step', 2, args_3.get('output_path'))
	assert steps[5].get('args').get('output_path') == args_3.get('output_path')
	assert steps[5].get('status') == 'drafted'
	assert args_2.get('target_path') == 'target-2.jpg'
	assert count_step_total('job-test-remix-step') == 6


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
	args_3 =\
	{
		'source_path': 'source-3.jpg',
		'target_path': 'target-3.jpg',
		'output_path': 'output-3.jpg'
	}
	args_4 =\
	{
		'source_path': 'source-4.jpg',
		'target_path': 'target-4.mp4',
		'output_path': 'output-sequence-4'
	}

	assert insert_step('job-invalid', 0, args_1) is False

	create_job('job-test-insert-step')
	add_step('job-test-insert-step', args_1)
	add_step('job-test-insert-step', args_1)

	assert insert_step('job-test-insert-step', 99, args_1) is False
	assert insert_step('job-test-insert-step', 0, args_2) is True
	assert insert_step('job-test-insert-step', -1, args_3) is True
	assert insert_step('job-test-insert-step', 2, args_4) is True

	steps = get_steps('job-test-insert-step')

	assert steps[0].get('args') == args_2
	assert steps[1].get('args') == args_1
	assert steps[2].get('args') == args_4
	assert steps[3].get('args') == args_3
	assert steps[4].get('args') == args_1
	assert steps[3].get('status') == 'drafted'
	assert count_step_total('job-test-insert-step') == 5


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
	args_3 =\
	{
		'source_path': 'source-3.jpg',
		'target_path': 'target-3.jpg',
		'output_path': 'output-3.jpg'
	}

	assert remove_step('job-invalid', 0) is False

	create_job('job-test-remove-step')
	add_step('job-test-remove-step', args_1)
	add_step('job-test-remove-step', args_2)
	add_step('job-test-remove-step', args_1)
	add_step('job-test-remove-step', args_3)

	assert remove_step('job-test-remove-step', 99) is False
	assert remove_step('job-test-remove-step', 0) is True
	assert remove_step('job-test-remove-step', -1) is True

	steps = get_steps('job-test-remove-step')

	assert steps[0].get('args') == args_2
	assert steps[1].get('args') == args_1
	assert count_step_total('job-test-remove-step') == 2


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

	assert get_steps('job-invalid') == []

	create_job('job-test-get-steps')
	add_step('job-test-get-steps', args_1)
	add_step('job-test-get-steps', args_2)
	steps = get_steps('job-test-get-steps')

	assert steps[0].get('args') == args_1
	assert steps[1].get('args') == args_2
	assert count_step_total('job-test-get-steps') == 2


def test_count_step_total() -> None:
	args_1 =\
	{
		'source_path': 'source-1.jpg',
		'target_path': 'target-1.jpg',
		'output_path': 'output-1.jpg'
	}

	assert count_step_total('job-invalid') == 0

	create_job('job-test-count-step-total')

	assert count_step_total('job-test-count-step-total') == 0

	add_step('job-test-count-step-total', args_1)
	add_step('job-test-count-step-total', args_1)
	add_step('job-test-count-step-total', args_1)

	assert count_step_total('job-test-count-step-total') == 3


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

	assert set_step_status('job-invalid', 0, 'completed') is False

	create_job('job-test-set-step-status')
	add_step('job-test-set-step-status', args_1)
	add_step('job-test-set-step-status', args_2)

	assert set_step_status('job-test-set-step-status', 99, 'completed') is False
	assert set_step_status('job-test-set-step-status', -1, 'completed') is False
	assert set_step_status('job-test-set-step-status', 0, 'completed') is True
	assert set_step_status('job-test-set-step-status', 1, 'failed') is True

	steps = get_steps('job-test-set-step-status')

	assert steps[0].get('status') == 'completed'
	assert steps[1].get('status') == 'failed'
	assert count_step_total('job-test-set-step-status') == 2


def test_set_steps_status() -> None:
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

	assert set_steps_status('job-invalid', 'queued') is False

	create_job('job-test-set-steps-status')
	add_step('job-test-set-steps-status', args_1)
	add_step('job-test-set-steps-status', args_2)

	assert set_steps_status('job-test-set-steps-status', 'queued') is True

	steps = get_steps('job-test-set-steps-status')

	assert steps[0].get('status') == 'queued'
	assert steps[1].get('status') == 'queued'
	assert count_step_total('job-test-set-steps-status') == 2


def test_read_job_file() -> None:
	assert read_job_file('job-invalid') is None

	create_job('job-test-read-job-file')
	move_job_file('job-test-read-job-file', 'completed')

	assert read_job_file('job-test-read-job-file').get('version') == '1'
	assert read_job_file('job-test-read-job-file').get('steps') == []


def test_update_job_file() -> None:
	assert update_job_file('job-invalid', read_job_file('job-invalid')) is False

	create_job('job-test-update-job-file')
	job = read_job_file('job-test-update-job-file')
	job['version'] = '2'

	assert update_job_file('job-test-update-job-file', job) is True
	assert read_job_file('job-test-update-job-file').get('version') == '2'
	assert read_job_file('job-test-update-job-file').get('date_updated') == job.get('date_updated')
	assert read_job_file('job-test-update-job-file').get('date_created') < read_job_file('job-test-update-job-file').get('date_updated')


def test_move_job_file() -> None:
	assert move_job_file('job-invalid', 'queued') is False

	create_job('job-test-move-job-file')

	assert move_job_file('job-test-move-job-file', 'queued') is True
	assert is_test_job_file('job-test-move-job-file.json', 'drafted') is False
	assert is_test_job_file('job-test-move-job-file.json', 'queued') is True
	assert move_job_file('job-test-move-job-file', 'failed') is True
	assert is_test_job_file('job-test-move-job-file.json', 'queued') is False
	assert is_test_job_file('job-test-move-job-file.json', 'failed') is True


def test_suggest_job_path() -> None:
	assert suggest_job_path('job-test-suggest-job-path', 'drafted') == get_test_job_file('job-test-suggest-job-path.json', 'drafted')
	assert suggest_job_path('job-test-suggest-job-path', 'completed') == get_test_job_file('job-test-suggest-job-path.json', 'completed')
	assert suggest_job_path('', 'drafted') is None


def test_find_job_path() -> None:
	assert find_job_path('job-invalid') is None
	assert find_job_path('') is None

	create_job('job-test-find-job-path')

	assert find_job_path('job-test-find-job-path') == get_test_job_file('job-test-find-job-path.json', 'drafted')

	move_job_file('job-test-find-job-path', 'failed')

	assert find_job_path('job-test-find-job-path') == get_test_job_file('job-test-find-job-path.json', 'failed')


def test_get_job_file_name() -> None:
	assert get_job_file_name('job-test-get-job-file-name') == 'job-test-get-job-file-name.json'
	assert get_job_file_name('../invalid') == hashlib.sha1('../invalid'.encode()).hexdigest() + '.json'
	assert get_job_file_name('') is None
