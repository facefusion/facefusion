from facefusion.types import ProcessState

PROCESS_STATE : ProcessState = 'pending'


def get_process_state() -> ProcessState:
	return PROCESS_STATE


def set_process_state(process_state : ProcessState) -> None:
	global PROCESS_STATE

	PROCESS_STATE = process_state


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
