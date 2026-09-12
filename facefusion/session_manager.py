import secrets
from datetime import datetime, timedelta
from typing import Dict
from typing import Optional

from facefusion.session_context import get_session_id, set_session_id
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


def fork_session() -> SessionId:
	fork_id = secrets.token_urlsafe(16)
	owner_id = get_session_id()
	session : Session =\
	{
		'owner_id': owner_id,
		'created_at': datetime.now()
	}

	set_session_id(fork_id)
	set_session(fork_id, session)

	return fork_id


def join_session() -> None:
	fork_id = get_session_id()
	owner_id = resolve_owner_id()

	clear_session(fork_id)
	set_session_id(owner_id)


def get_session(session_id : SessionId) -> Optional[Session]:
	return SESSIONS.get(session_id)


def find_session_id(access_token : str) -> Optional[SessionId]:
	for session_id, session in SESSIONS.items():
		if session.get('access_token') == access_token:
			return session_id
	return None


def resolve_owner_id() -> SessionId:
	session_id = get_session_id()
	session = get_session(session_id)

	if session and session.get('owner_id'):
		return session.get('owner_id')

	return session_id


def set_session(session_id : SessionId, session : Session) -> None:
	SESSIONS[session_id] = session


def validate_session(session_id : SessionId) -> bool:
	session = get_session(session_id)
	return session and datetime.now() < session.get('expires_at')


def clear_session(session_id : SessionId) -> None:
	if session_id in SESSIONS:
		del SESSIONS[session_id]
