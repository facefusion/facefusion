import secrets
from datetime import datetime, timedelta
from typing import Iterator

import pytest

from facefusion.session_context import get_session_id, resolve_local_id, set_session_id
from facefusion.session_manager import clear_session, create_session, fork_session, get_session, join_session, resolve_owner_id, set_session, validate_session


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
	assert get_session(fork_id).get('owner_id') == local_id
	assert get_session(fork_id).get('access_token') is None
	assert get_session(fork_id).get('expires_at') is None

	join_session()


def test_get_and_set_session() -> None:
	session = create_session()
	session_id = secrets.token_urlsafe(16)

	set_session(session_id, session)

	assert get_session(session_id) == session


def test_resolve_owner_id() -> None:
	local_id = resolve_local_id()

	assert resolve_owner_id() == local_id

	set_session('session-a', create_session())
	set_session('session-a1', { 'owner_id': 'session-a', 'created_at': datetime.now() })
	set_session_id('session-a')

	assert resolve_owner_id() == 'session-a'

	set_session_id('session-a1')

	assert resolve_owner_id() == 'session-a'

	clear_session('session-a1')
	clear_session('session-a')


def test_validate_session() -> None:
	session = create_session()
	session_id = secrets.token_urlsafe(16)

	set_session(session_id, session)

	assert validate_session(session_id) is True

	set_session(session_id,
	{
		'access_token': session.get('access_token'),
		'refresh_token': session.get('refresh_token'),
		'created_at': session.get('created_at'),
		'expires_at': session.get('expires_at') - timedelta(hours = 1)
	})

	assert validate_session(session_id) is False


def test_clear_session() -> None:
	session = create_session()
	session_id = secrets.token_urlsafe(16)

	set_session(session_id, session)

	assert validate_session(session_id) is True

	clear_session(session_id)

	assert validate_session(session_id) is None


def test_join_session() -> None:
	local_id = resolve_local_id()
	fork_id = fork_session()
	join_session()

	assert get_session_id() == local_id
	assert get_session(fork_id) is None
