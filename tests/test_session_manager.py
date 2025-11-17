import secrets
from datetime import timedelta

from facefusion.session_manager import clear_session, create_session, get_session, set_session, validate_session


def test_get_and_set_session() -> None:
	session = create_session()
	session_id = secrets.token_urlsafe(16)

	set_session(session_id, session)

	assert get_session(session_id) == session


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
