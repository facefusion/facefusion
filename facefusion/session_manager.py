from typing import Dict
from typing import Optional

from facefusion.types import Session


SESSIONS : Dict[str, Session] = {}


def get_session(key : str) -> Optional[Session]:
	return SESSIONS.get(key)


def set_session(key : str, session : Session) -> None:
	SESSIONS[key] = session


def clear_session(key : str) -> None:
	del SESSIONS[key]
