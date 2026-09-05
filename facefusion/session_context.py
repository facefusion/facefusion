import getpass
import hashlib
import secrets
from contextvars import ContextVar
from typing import Optional

from facefusion.types import SessionId

SESSION_ID : ContextVar[Optional[SessionId]] = ContextVar('SESSION_ID', default = None)


def set_session_id(session_id : SessionId) -> None:
	SESSION_ID.set(session_id)


def get_session_id() -> SessionId:
	session_id = SESSION_ID.get()

	if session_id:
		return session_id
	return resolve_process_id()


def clear_session_id() -> None:
	SESSION_ID.set(None)


def resolve_step_id(session_id : SessionId) -> SessionId:
	return '.'.join([ session_id, secrets.token_urlsafe(16) ])


def resolve_owner_id() -> SessionId:
	return get_session_id().split('.')[0]


def resolve_process_id() -> SessionId:
	return hashlib.sha1(getpass.getuser().encode()).hexdigest()
