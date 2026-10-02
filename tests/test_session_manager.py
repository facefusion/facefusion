import secrets
import threading
from datetime import datetime, timedelta
from typing import Iterator, List

import pytest

from facefusion.session_context import get_session_id, resolve_local_id, set_session_id
from facefusion.session_manager import clear_api_session, clear_cli_session, conditional_clear_api_session, conditional_clear_cli_session, count_api_sessions, create_api_session, create_cli_session, find_api_session_id, fork_session, get_api_session, get_cli_session, join_session, observe_api_session, observe_cli_session, resolve_owner_id, set_api_session, set_cli_session, validate_api_session, validate_cli_session


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = resolve_local_id()

	set_session_id(local_id)

	yield

	set_session_id(local_id)


def join_observe_threads(threads : List[threading.Thread], timeout : float) -> None:
	for thread in threading.enumerate():
		if thread not in threads:
			thread.join(timeout = timeout)


def test_create_api_session() -> None:
	api_session = create_api_session()

	assert len(api_session.get('access_token')) == 86
	assert len(api_session.get('refresh_token')) == 86
	assert not api_session.get('access_token') == api_session.get('refresh_token')
	assert not api_session.get('access_token') == create_api_session().get('access_token')
	assert api_session.get('expires_at') - api_session.get('created_at') > timedelta(minutes = 9)
	assert api_session.get('expires_at') - api_session.get('created_at') < timedelta(minutes = 11)


def test_create_cli_session() -> None:
	local_id = resolve_local_id()

	assert create_cli_session().get('owner_id') == local_id

	set_session_id('session-a')

	assert create_cli_session().get('owner_id') == 'session-a'


def test_observe_api_session() -> None:
	api_session = create_api_session()
	session_id = secrets.token_urlsafe(16)
	threads = threading.enumerate()

	set_api_session(session_id, api_session)
	observe_api_session(session_id)
	join_observe_threads(threads, 1.5)

	assert get_api_session(session_id) == api_session

	api_session['expires_at'] = datetime.now() - timedelta(hours = 1)
	join_observe_threads(threads, 3.0)

	assert get_api_session(session_id) is None


def test_observe_cli_session() -> None:
	local_id = resolve_local_id()
	session_id = secrets.token_urlsafe(16)
	threads = threading.enumerate()

	set_api_session(session_id, create_api_session())
	set_session_id(session_id)
	fork_id = fork_session()
	set_session_id(local_id)
	observe_cli_session(fork_id)
	join_observe_threads(threads, 1.5)

	assert get_cli_session(fork_id).get('owner_id') == session_id

	clear_api_session(session_id)
	join_observe_threads(threads, 3.0)

	assert get_cli_session(fork_id) is None


def test_fork_session() -> None:
	local_id = resolve_local_id()
	fork_id = fork_session()

	assert get_session_id() == fork_id
	assert resolve_owner_id() == local_id
	assert get_cli_session(fork_id).get('owner_id') == local_id

	join_session()

	assert not fork_session() == fork_id

	join_session()


def test_join_session() -> None:
	local_id = resolve_local_id()
	fork_id = fork_session()
	join_session()

	assert get_session_id() == local_id
	assert get_cli_session(fork_id) is None

	set_api_session('session-a', create_api_session())
	set_session_id('session-a')
	fork_id = fork_session()
	join_session()

	assert get_session_id() == 'session-a'
	assert get_cli_session(fork_id) is None

	clear_api_session('session-a')


def test_get_and_set_api_session() -> None:
	api_session = create_api_session()
	session_id = secrets.token_urlsafe(16)

	set_api_session(session_id, api_session)

	assert get_api_session(session_id) == api_session

	clear_api_session(session_id)


def test_get_and_set_cli_session() -> None:
	local_id = resolve_local_id()
	cli_session = create_cli_session()
	session_id = secrets.token_urlsafe(16)

	set_cli_session(session_id, cli_session)

	assert get_cli_session(session_id) == cli_session
	assert get_cli_session(session_id).get('owner_id') == local_id

	set_session_id(session_id)

	assert get_cli_session('invalid') is None

	clear_cli_session(session_id)


def test_find_api_session_id() -> None:
	api_session = create_api_session()
	session_id = secrets.token_urlsafe(16)

	set_api_session(session_id, api_session)

	assert find_api_session_id(api_session.get('access_token')) == session_id
	assert find_api_session_id(api_session.get('access_token') + 'invalid') is None
	assert find_api_session_id('invalid') is None

	clear_api_session(session_id)


def test_count_api_sessions() -> None:
	session_total = count_api_sessions()
	api_session = create_api_session()
	session_id = secrets.token_urlsafe(16)

	set_api_session(session_id, api_session)

	assert count_api_sessions() == session_total + 1

	api_session['expires_at'] = datetime.now() - timedelta(hours = 1)

	assert count_api_sessions() == session_total

	clear_api_session(session_id)

	assert count_api_sessions() == session_total


def test_resolve_owner_id() -> None:
	local_id = resolve_local_id()

	assert resolve_owner_id() == local_id

	set_api_session('session-a', create_api_session())
	set_session_id('session-a')

	assert resolve_owner_id() == 'session-a'

	fork_session()

	assert resolve_owner_id() == 'session-a'

	join_session()
	clear_api_session('session-a')


def test_validate_api_session() -> None:
	api_session = create_api_session()
	session_id = secrets.token_urlsafe(16)

	set_api_session(session_id, api_session)

	assert validate_api_session(session_id) is True

	set_api_session(session_id,
	{
		'access_token': api_session.get('access_token'),
		'refresh_token': api_session.get('refresh_token'),
		'created_at': api_session.get('created_at'),
		'expires_at': api_session.get('expires_at') - timedelta(hours = 1)
	})

	assert validate_api_session(session_id) is False

	clear_api_session(session_id)

	assert validate_api_session(session_id) is False


def test_validate_cli_session() -> None:
	local_fork_id = fork_session()

	assert validate_cli_session(local_fork_id) is True

	join_session()

	assert validate_cli_session(local_fork_id) is False

	session_id = secrets.token_urlsafe(16)

	set_api_session(session_id, create_api_session())
	set_session_id(session_id)
	fork_id = fork_session()

	assert validate_cli_session(fork_id) is True

	clear_api_session(session_id)

	assert validate_cli_session(fork_id) is False

	clear_cli_session(fork_id)


def test_clear_api_session() -> None:
	api_session = create_api_session()
	session_id = secrets.token_urlsafe(16)

	set_api_session(session_id, api_session)
	clear_api_session(session_id)

	assert get_api_session(session_id) is None


def test_clear_cli_session() -> None:
	cli_session = create_cli_session()
	session_id = secrets.token_urlsafe(16)

	set_cli_session(session_id, cli_session)
	clear_cli_session(session_id)

	assert get_cli_session(session_id) is None


def test_conditional_clear_api_session() -> None:
	api_session = create_api_session()
	session_id = secrets.token_urlsafe(16)

	api_session['expires_at'] = datetime.now() - timedelta(hours = 1)
	set_api_session(session_id, api_session)
	conditional_clear_api_session(session_id)

	assert get_api_session(session_id) is None


def test_conditional_clear_cli_session() -> None:
	session_id = secrets.token_urlsafe(16)

	set_api_session(session_id, create_api_session())
	set_session_id(session_id)
	fork_id = fork_session()
	clear_api_session(session_id)
	conditional_clear_cli_session(fork_id)

	assert get_cli_session(fork_id) is None
