import pytest

from facefusion.job_manager import clear_jobs, init_jobs


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	clear_jobs('.jobs')
	init_jobs('.jobs')


@pytest.mark.skip()
def test_job_create() -> None:
	pass


@pytest.mark.skip()
def test_job_create_invalid() -> None:
	pass


@pytest.mark.skip()
def test_job_delete() -> None:
	pass


@pytest.mark.skip()
def test_job_delete_invalid() -> None:
	pass


@pytest.mark.skip()
def test_job_add_step() -> None:
	pass


@pytest.mark.skip()
def test_job_add_step_invalid() -> None:
	pass


@pytest.mark.skip()
def test_job_remix() -> None:
	pass


@pytest.mark.skip()
def test_job_remix_invalid() -> None:
	pass


@pytest.mark.skip()
def test_job_insert_step() -> None:
	pass


@pytest.mark.skip()
def test_job_insert_step_invalid() -> None:
	pass


@pytest.mark.skip()
def test_job_remove_step() -> None:
	pass


@pytest.mark.skip()
def test_job_run() -> None:
	pass


@pytest.mark.skip()
def test_job_run_invalid() -> None:
	pass


@pytest.mark.skip()
def test_job_run_all() -> None:
	pass


@pytest.mark.skip()
def test_job_run_all_invalid() -> None:
	pass
