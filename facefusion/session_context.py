from contextvars import ContextVar
from typing import Optional

from facefusion.types import SessionId

SESSION_ID : ContextVar[Optional[SessionId]] = ContextVar('SESSION_ID', default = None)


def set_session_id(session_id : SessionId) -> None:
	SESSION_ID.set(session_id)


def get_session_id() -> Optional[SessionId]:
	return SESSION_ID.get()


def clear_session_id() -> None:
	SESSION_ID.set(None)
