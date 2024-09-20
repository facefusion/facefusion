from time import sleep

import pytest

from facefusion.jobs.job_list import compose_job_list
from facefusion.jobs.job_manager import clear_jobs, create_job, init_jobs
from .helper import get_test_jobs_directory


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(get_test_jobs_directory())


def test_compose_job_list() -> None:
	create_job('job-test-compose-job-list-1')
	sleep(0.5)
	create_job('job-test-compose-job-list-2')
	job_headers, job_contents = compose_job_list('drafted')

	assert job_headers == [ 'job id', 'steps', 'date created', 'date updated', 'job status' ]
	assert job_contents[0] == [ 'job-test-compose-job-list-1', 0, 'just now', None, 'drafted' ]
	assert job_contents[1] == [ 'job-test-compose-job-list-2', 0, 'just now', None, 'drafted' ]
