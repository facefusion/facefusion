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
	assert len(compose_job_list('drafted')[1]) == 1
	create_job('job-test-compose-job-list-2')
	assert len(compose_job_list('drafted')[1]) == 2
	create_job('job-test-compose-job-list-3')
	assert len(compose_job_list('drafted')[1]) == 3
