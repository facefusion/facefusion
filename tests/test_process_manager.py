from typing import Iterator

import pytest

from facefusion import session_context, store_creator
from facefusion.process_manager import PROCESS_STORE, check, clear, destroy, end, get_state, init, is_checking, is_pending, is_processing, is_stopping, set_state, start, stop


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = session_context.resolve_local_id()

	session_context.set_session_id('session-a')
	clear()
	session_context.set_session_id('session-b')
	clear()
	session_context.set_session_id('session-a')

	yield

	session_context.set_session_id(local_id)


def test_init() -> None:
	set_state('processing')
	init()

	assert get_state() == 'pending'


def test_get_state() -> None:
	set_state('processing')
	session_context.set_session_id('session-b')
	set_state('stopping')

	assert get_state() == 'stopping'

	session_context.set_session_id('session-a')

	assert get_state() == 'processing'


def test_is_checking() -> None:
	set_state('checking')

	assert is_checking() is True

	set_state('pending')

	assert is_checking() is False


def test_is_processing() -> None:
	set_state('processing')

	assert is_processing() is True

	set_state('pending')

	assert is_processing() is False


def test_is_stopping() -> None:
	set_state('stopping')

	assert is_stopping() is True

	set_state('pending')

	assert is_stopping() is False


def test_is_pending() -> None:
	set_state('pending')

	assert is_pending() is True

	set_state('processing')

	assert is_pending() is False


def test_set_state() -> None:
	set_state('checking')

	assert get_state() == 'checking'

	session_context.set_session_id('session-b')

	assert get_state() == 'pending'


def test_check() -> None:
	set_state('pending')
	check()

	assert get_state() == 'checking'


def test_start() -> None:
	set_state('pending')
	start()

	assert get_state() == 'processing'


def test_stop() -> None:
	set_state('processing')
	stop()

	assert get_state() == 'stopping'


def test_end() -> None:
	set_state('processing')
	end()

	assert get_state() == 'pending'


def test_clear() -> None:
	set_state('processing')
	clear()

	assert get_state() == 'pending'


def test_destroy() -> None:
	destroy('session-a')

	assert store_creator.has_content(PROCESS_STORE, 'session-a') is False
	assert store_creator.has_content(PROCESS_STORE, 'session-b') is True
