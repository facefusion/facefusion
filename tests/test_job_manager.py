import pytest

from facefusion.job_manager import init_jobs, clear_jobs


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	clear_jobs('.jobs')
	init_jobs('.jobs')


@pytest.mark.skip()
def test_create_job() -> None:
	pass


@pytest.mark.skip()
def test_delete_job() -> None:
	pass


@pytest.mark.skip()
def test_get_job_status() -> None:
	pass


@pytest.mark.skip()
def test_find_job_ids() -> None:
	pass


@pytest.mark.skip()
def test_add_step() -> None:
	pass


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


@pytest.mark.skip()
def test_set_step_action() -> None:
	pass
