from facefusion import store_creator
from facefusion.session_context import get_session_id, resolve_local_id
from facefusion.session_manager import resolve_owner_id
from facefusion.types import ProcessState, SessionId, Store

PROCESS_STORE : Store = store_creator.create_store('pending')


def init() -> None:
	session_id = get_session_id()
	store_creator.init_content(PROCESS_STORE, session_id)


def get_state() -> ProcessState:
	owner_id = resolve_owner_id()
	local_id = resolve_local_id()

	if store_creator.get_content(PROCESS_STORE, local_id) == 'stopping':
		return 'stopping'

	return store_creator.get_content(PROCESS_STORE, owner_id)


def is_checking() -> bool:
	return get_state() == 'checking'


def is_processing() -> bool:
	return get_state() == 'processing'


def is_stopping() -> bool:
	return get_state() == 'stopping'


def is_pending() -> bool:
	return get_state() == 'pending'


def set_state(process_state : ProcessState) -> None:
	owner_id = resolve_owner_id()
	store_creator.set_content(PROCESS_STORE, owner_id, process_state)


def check() -> None:
	set_state('checking')


def start() -> None:
	set_state('processing')


def stop() -> None:
	set_state('stopping')


def end() -> None:
	set_state('pending')


def clear() -> None:
	session_id = get_session_id()
	store_creator.init_content(PROCESS_STORE, session_id)


def destroy(session_id : SessionId) -> None:
	store_creator.delete_content(PROCESS_STORE, session_id)

