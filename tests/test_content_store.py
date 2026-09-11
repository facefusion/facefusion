import pytest

from facefusion import session_context, store_creator
from facefusion.content_store import CONTENT_STORE, calculate_rate, clear, get_hit, init, set_hit, tick


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	local_id = session_context.resolve_local_id()

	session_context.set_session_id(local_id)
	init()


def test_init() -> None:
	local_id = session_context.resolve_local_id()

	session_context.set_session_id('session-a')
	init()
	set_hit()

	assert get_hit() == 1

	session_context.set_session_id(local_id)

	assert get_hit() == 0


def test_get_hit() -> None:
	assert get_hit() == 0

	set_hit()

	assert get_hit() == 1


def test_set_hit() -> None:
	set_hit()
	set_hit()

	assert get_hit() == 2


def test_calculate_rate() -> None:
	assert calculate_rate() == 0.0

	for _ in range(100):
		tick()

	set_hit()

	assert calculate_rate() == 30.0


def test_clear() -> None:
	local_id = session_context.resolve_local_id()

	tick()
	set_hit()
	clear()

	assert store_creator.has_content(CONTENT_STORE, local_id) is False
