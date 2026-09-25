import secrets
from datetime import timedelta
from typing import Iterator

import pytest

from facefusion.session_context import get_session_id, resolve_local_id, set_session_id
from facefusion.session_manager import clear_api_session, clear_cli_session, create_api_session, create_cli_session, find_api_session_id, fork_session, get_api_session, get_cli_session, join_session, resolve_owner_id, set_api_session, set_cli_session, validate_api_session, validate_cli_session


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = resolve_local_id()

	set_session_id(local_id)

	yield

	set_session_id(local_id)


def test_fork_session() -> None:
	local_id = resolve_local_id()
	fork_id = fork_session()

	assert get_session_id() == fork_id
	assert resolve_owner_id() == local_id
	assert get_cli_session(fork_id).get('owner_id') == local_id

	join_session()


def test_join_session() -> None:
	local_id = resolve_local_id()
	fork_id = fork_session()
	join_session()

	assert get_session_id() == local_id
	assert get_cli_session(fork_id) is None


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

	clear_cli_session(session_id)


def test_find_api_session_id() -> None:
	api_session = create_api_session()
	session_id = secrets.token_urlsafe(16)

	set_api_session(session_id, api_session)

	assert find_api_session_id(api_session.get('access_token')) == session_id
	assert find_api_session_id('INVALID') is None

	clear_api_session(session_id)


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
