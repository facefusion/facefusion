from datetime import datetime
from typing import Dict
from typing import Optional

from facefusion.types import Session


SESSIONS : Dict[str, Session] = {}


def get_session(key : str) -> Optional[Session]:
	return SESSIONS.get(key)


def set_session(key : str, session : Session) -> None:
	SESSIONS[key] = session


def validate_session(key : str) -> bool:
	session = get_session(key)
	return session and datetime.now() <= session.get('expires_at')


def clear_session(key : str) -> None:
	if key in SESSIONS:
		del SESSIONS[key]

