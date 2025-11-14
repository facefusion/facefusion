import secrets
from datetime import timedelta

from facefusion.session_manager import clear_session, create_session, get_session, set_session, validate_session


def test_get_and_set_session() -> None:
	session = create_session()
	access_token = secrets.token_urlsafe(128)

	set_session(access_token, session)

	assert get_session(access_token) == session


def test_validate_session() -> None:
	session = create_session()
	access_token = secrets.token_urlsafe(128)

	set_session(access_token, session)

	assert validate_session(access_token) is True

	set_session(access_token,
	{
		'access_token': session.get('access_token'),
		'refresh_token': session.get('refresh_token'),
		'created_at': session.get('created_at'),
		'expires_at': session.get('expires_at') - timedelta(hours = 1)
	})

	assert validate_session(access_token) is False


def test_clear_session() -> None:
	session = create_session()
	access_token = secrets.token_urlsafe(128)

	set_session(access_token, session)

	assert validate_session(access_token) is True

	clear_session(access_token)

	assert validate_session(access_token) is None
