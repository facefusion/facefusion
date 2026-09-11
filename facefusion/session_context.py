import getpass
import hashlib
from contextvars import ContextVar
from functools import lru_cache
from typing import Optional

from facefusion.types import SessionId

SESSION_ID : ContextVar[Optional[SessionId]] = ContextVar('SESSION_ID', default = None)


def set_session_id(session_id : SessionId) -> None:
	SESSION_ID.set(session_id)


def get_session_id() -> SessionId:
	return SESSION_ID.get() or resolve_local_id()


def clear_session_id() -> None:
	SESSION_ID.set(None)


@lru_cache()
def resolve_local_id() -> SessionId:
	return hashlib.sha1(getpass.getuser().encode()).hexdigest()
