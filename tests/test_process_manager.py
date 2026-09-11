from typing import Iterator

import pytest

from facefusion import session_context
from facefusion.process_manager import clear, end, get_state, init, is_pending, is_processing, is_stopping, set_state, start, stop


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


def test_start() -> None:
	set_state('pending')
	start()

	assert is_processing()


def test_stop() -> None:
	set_state('processing')
	stop()

	assert is_stopping()


def test_end() -> None:
	set_state('processing')
	end()

	assert is_pending()


def test_clear() -> None:
	set_state('processing')
	clear()

	assert get_state() == 'pending'
