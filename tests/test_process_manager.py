import pytest

from facefusion.process_manager import clear_process_state, end, get_process_state, init_process_state, is_pending, is_processing, is_stopping, set_process_state, start, stop
from facefusion.session_context import set_session_id


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	set_session_id('session-a')
	clear_process_state()
	set_session_id('session-b')
	clear_process_state()
	set_session_id('session-a')


def test_init_process_state() -> None:
	assert get_process_state() is None

	init_process_state()

	assert get_process_state() == 'pending'


def test_get_process_state() -> None:
	set_process_state('processing')
	set_session_id('session-b')
	set_process_state('stopping')

	assert get_process_state() == 'stopping'

	set_session_id('session-a')

	assert get_process_state() == 'processing'


def test_clear_process_state() -> None:
	set_process_state('processing')
	clear_process_state()

	assert get_process_state() is None


def test_start() -> None:
	set_process_state('pending')
	start()

	assert is_processing()


def test_stop() -> None:
	set_process_state('processing')
	stop()

	assert is_stopping()


def test_end() -> None:
	set_process_state('processing')
	end()

	assert is_pending()
