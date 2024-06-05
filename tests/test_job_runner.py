import pytest

from facefusion.job_manager import init_jobs, clear_jobs


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	clear_jobs('.jobs')
	init_jobs('.jobs')


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
