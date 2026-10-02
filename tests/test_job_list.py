from datetime import datetime, timedelta
from time import sleep

import pytest

from facefusion import state_manager
from facefusion.jobs.job_list import compose_job_list, prepare_describe_datetime
from facefusion.jobs.job_manager import add_step, clear_jobs, create_job, init_jobs, move_job_file
from facefusion.json import write_json
from .assert_helper import get_test_job_file, get_test_jobs_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('jobs_path', get_test_jobs_directory())


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(state_manager.get_jobs_path())


def test_compose_job_list() -> None:
	args_1 =\
	{
		'source_path': 'source-1.jpg',
		'target_path': 'target-1.jpg',
		'output_path': 'output-1.jpg'
	}

	create_job('job-test-compose-job-list-1')
	sleep(0.5)
	create_job('job-test-compose-job-list-2')
	job_headers, job_contents = compose_job_list('drafted')

	assert job_headers == [ 'job id', 'steps', 'date created', 'date updated', 'job status' ]
	assert job_contents[0] == [ 'job-test-compose-job-list-1', 0, 'just now', None, 'drafted' ]
	assert job_contents[1] == [ 'job-test-compose-job-list-2', 0, 'just now', None, 'drafted' ]

	sleep(0.5)
	add_step('job-test-compose-job-list-1', args_1)
	add_step('job-test-compose-job-list-1', args_1)
	_, job_contents = compose_job_list('drafted')

	assert job_contents[0] == [ 'job-test-compose-job-list-2', 0, 'just now', None, 'drafted' ]
	assert job_contents[1] == [ 'job-test-compose-job-list-1', 2, 'just now', 'just now', 'drafted' ]

	move_job_file('job-test-compose-job-list-2', 'queued')
	write_json(get_test_job_file('job-test-compose-job-list-3.json', 'queued'),
	{
		'version': '1'
	})
	_, job_contents = compose_job_list('queued')

	assert job_contents == [ [ 'job-test-compose-job-list-2', 0, 'just now', None, 'queued' ] ]
	assert compose_job_list('failed') == ([ 'job id', 'steps', 'date created', 'date updated', 'job status' ], [])


def test_prepare_describe_datetime() -> None:
	assert prepare_describe_datetime(datetime.now().isoformat()) == 'just now'
	assert prepare_describe_datetime((datetime.now() - timedelta(minutes = 5)).isoformat()) == '5 minutes ago'
	assert prepare_describe_datetime((datetime.now() - timedelta(hours = 2, minutes = 30)).isoformat()) == '2 hours and 30 minutes ago'
	assert prepare_describe_datetime(None) is None
	assert prepare_describe_datetime('') is None
