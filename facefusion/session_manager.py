import secrets
import threading
from datetime import datetime, timedelta
from functools import partial
from time import sleep
from typing import Dict
from typing import Optional

from facefusion.session_context import get_session_id, set_session_id
from facefusion.types import ApiSession, CliSession, SessionId

API_SESSIONS : Dict[SessionId, ApiSession] = {}
CLI_SESSIONS : Dict[SessionId, CliSession] = {}


def create_api_session() -> ApiSession:
	api_session : ApiSession =\
	{
		'access_token': secrets.token_urlsafe(64),
		'refresh_token': secrets.token_urlsafe(64),
		'created_at': datetime.now(),
		'expires_at': datetime.now() + timedelta(minutes = 10)
	}

	return api_session


def create_cli_session() -> CliSession:
	cli_session : CliSession =\
	{
		'owner_id': get_session_id(),
		'created_at': datetime.now()
	}

	return cli_session


def observe_api_session(session_id : SessionId) -> None:
	threading.Thread(
		target = partial(conditional_clear_api_session, session_id),
		daemon = True
	).start()


def fork_session() -> SessionId:
	fork_id = secrets.token_urlsafe(16)
	cli_session = create_cli_session()

	set_cli_session(fork_id, cli_session)
	set_session_id(fork_id)

	return fork_id


def join_session() -> None:
	fork_id = get_session_id()
	owner_id = resolve_owner_id()

	clear_cli_session(fork_id)
	set_session_id(owner_id)


def get_api_session(session_id : SessionId) -> Optional[ApiSession]:
	return API_SESSIONS.get(session_id)


def get_cli_session(session_id : SessionId) -> Optional[CliSession]:
	return CLI_SESSIONS.get(session_id)


def find_api_session_id(access_token : str) -> Optional[SessionId]:
	for session_id, api_session in API_SESSIONS.items():
		if api_session.get('access_token') == access_token:
			return session_id
	return None


def count_api_sessions() -> int:
	session_total = 0

	for session_id in API_SESSIONS:
		if validate_api_session(session_id):
			session_total += 1

	return session_total


def resolve_owner_id() -> SessionId:
	session_id = get_session_id()
	cli_session = get_cli_session(session_id)

	if cli_session:
		return cli_session.get('owner_id')

	return session_id


def set_api_session(session_id : SessionId, api_session : ApiSession) -> None:
	API_SESSIONS[session_id] = api_session


def set_cli_session(session_id : SessionId, cli_session : CliSession) -> None:
	CLI_SESSIONS[session_id] = cli_session


def validate_api_session(session_id : SessionId) -> bool:
	api_session = get_api_session(session_id)

	if api_session:
		return datetime.now() < api_session.get('expires_at')

	return False


def clear_api_session(session_id : SessionId) -> None:
	if session_id in API_SESSIONS:
		del API_SESSIONS[session_id]


def clear_cli_session(session_id : SessionId) -> None:
	if session_id in CLI_SESSIONS:
		del CLI_SESSIONS[session_id]


def conditional_clear_api_session(session_id : SessionId) -> None:
	while validate_api_session(session_id):
		sleep(1)

	clear_api_session(session_id)
