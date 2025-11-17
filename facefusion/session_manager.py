import secrets
from datetime import datetime, timedelta
from typing import Dict
from typing import Optional

from facefusion.types import Session, Token

SESSIONS : Dict[Token, Session] = {}


def create_session() -> Session:
	session : Session =\
	{
		'access_token': secrets.token_urlsafe(128),
		'refresh_token': secrets.token_urlsafe(128),
		'created_at': datetime.now(),
		'expires_at': datetime.now() + timedelta(minutes = 10)
	}

	return session


def get_session(access_token : Token) -> Optional[Session]:
	return SESSIONS.get(access_token)


def set_session(access_token : Token, session : Session) -> None:
	SESSIONS[access_token] = session


def validate_session(access_token : Token) -> bool:
	session = get_session(access_token)
	return session and datetime.now() <= session.get('expires_at')


def clear_session(access_token : Token) -> None:
	if access_token in SESSIONS:
		del SESSIONS[access_token]

