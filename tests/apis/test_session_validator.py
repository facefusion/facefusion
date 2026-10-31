import secrets
from datetime import timedelta

from facefusion.apis.session_validator import validate_access_token
from facefusion.session_manager import clear_api_session, create_api_session, set_api_session, validate_api_session


def test_validate_access_token() -> None:
	api_session = create_api_session()
	session_id = secrets.token_urlsafe(16)

	set_api_session(session_id, api_session)

	assert validate_access_token(session_id) is True

	set_api_session(session_id,
	{
		'access_token': api_session.get('access_token'),
		'refresh_token': api_session.get('refresh_token'),
		'created_at': api_session.get('created_at') - timedelta(minutes = 4),
		'expires_at': api_session.get('expires_at') - timedelta(minutes = 4)
	})

	assert validate_access_token(session_id) is True

	set_api_session(session_id,
	{
		'access_token': api_session.get('access_token'),
		'refresh_token': api_session.get('refresh_token'),
		'created_at': api_session.get('created_at') - timedelta(minutes = 6),
		'expires_at': api_session.get('expires_at') - timedelta(minutes = 6)
	})

	assert validate_access_token(session_id) is False
	assert validate_api_session(session_id) is True

	clear_api_session(session_id)

	assert validate_access_token(session_id) is False
