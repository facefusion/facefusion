import pytest

from facefusion.session_context import get_session_id, resolve_local_id, set_session_id


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	local_id = resolve_local_id()
	set_session_id(local_id)


def test_get_session_id() -> None:
	assert get_session_id() == resolve_local_id()

	set_session_id('session-a')

	assert get_session_id() == 'session-a'


def test_resolve_local_id() -> None:
	assert resolve_local_id() == resolve_local_id()
