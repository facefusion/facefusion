import secrets
from datetime import datetime, timedelta
from typing import Dict
from typing import Optional

from facefusion.types import Session, SessionId

SESSIONS : Dict[SessionId, Session] = {}


def create_session() -> Session:
	session : Session =\
	{
		'access_token': secrets.token_urlsafe(64),
		'refresh_token': secrets.token_urlsafe(64),
		'created_at': datetime.now(),
		'expires_at': datetime.now() + timedelta(minutes = 10)
	}

	return session


def get_session(session_id : SessionId) -> Optional[Session]:
	return SESSIONS.get(session_id)


def find_session_id(access_token : str) -> Optional[SessionId]:
	for session_id, session in SESSIONS.items():
		if session.get('access_token') == access_token:
			return session_id
	return None


def set_session(session_id : SessionId, session : Session) -> None:
	SESSIONS[session_id] = session


def validate_session(session_id : SessionId) -> bool:
	session = get_session(session_id)
	return session and datetime.now() <= session.get('expires_at')


def clear_session(session_id : SessionId) -> None:
	if session_id in SESSIONS:
		del SESSIONS[session_id]

