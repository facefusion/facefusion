import pytest

from facefusion import session_context, store_creator
from facefusion.content_store import CONTENT_STORE, calculate_rate, clear, destroy, get_hit, init, set_hit, tick


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	local_id = session_context.resolve_local_id()

	session_context.set_session_id(local_id)
	init()


def test_init() -> None:
	local_id = session_context.resolve_local_id()

	session_context.set_session_id('session-a')
	init()
	tick()
	set_hit()

	assert get_hit() == 1
	assert calculate_rate() == 3000.0

	session_context.set_session_id(local_id)

	assert get_hit() == 0
	assert calculate_rate() == 0.0

	set_hit()

	assert calculate_rate() == 0.0


def test_tick() -> None:
	for _ in range(29):
		assert tick() is False

	assert tick() is True
	assert tick(2) is False
	assert tick(2) is True


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
	assert calculate_rate(10) == 10.0


def test_clear() -> None:
	tick()
	set_hit()
	clear()

	assert get_hit() == 0
	assert calculate_rate() == 0.0


def test_destroy() -> None:
	local_id = session_context.resolve_local_id()

	set_hit()
	session_context.set_session_id('session-a')
	init()
	set_hit()
	session_context.set_session_id(local_id)
	destroy('session-a')

	assert store_creator.has_content(CONTENT_STORE, 'session-a') is False
	assert get_hit() == 1

	destroy('session-a')

	assert store_creator.has_content(CONTENT_STORE, 'session-a') is False
