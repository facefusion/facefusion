from facefusion import store_creator
from facefusion.session_context import get_session_id
from facefusion.types import ProcessState, Store

PROCESS_STORE : Store = store_creator.create_store('pending')


def init_process_state() -> None:
	store_creator.init_content(PROCESS_STORE, get_session_id())


def get_process_state() -> ProcessState:
	return store_creator.get_content(PROCESS_STORE, get_session_id())


def set_process_state(process_state : ProcessState) -> None:
	store_creator.set_content(PROCESS_STORE, get_session_id(), process_state)


def clear_process_state() -> None:
	store_creator.delete_content(PROCESS_STORE, get_session_id())


def is_checking() -> bool:
	return get_process_state() == 'checking'


def is_processing() -> bool:
	return get_process_state() == 'processing'


def is_stopping() -> bool:
	return get_process_state() == 'stopping'


def is_pending() -> bool:
	return get_process_state() == 'pending'


def check() -> None:
	set_process_state('checking')


def start() -> None:
	set_process_state('processing')


def stop() -> None:
	set_process_state('stopping')


def end() -> None:
	set_process_state('pending')
