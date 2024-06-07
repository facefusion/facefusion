import pytest

from facefusion.job_manager import init_jobs, clear_jobs
from .helper import get_test_jobs_directory


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(get_test_jobs_directory())


@pytest.mark.skip()
def test_run_job() -> None:
	pass


@pytest.mark.skip()
def test_run_all_job() -> None:
	pass


@pytest.mark.skip()
def test_run_steps() -> None:
	pass


@pytest.mark.skip()
def test_merge_steps() -> None:
	pass


@pytest.mark.skip()
def test_collect_merge_set() -> None:
	pass
