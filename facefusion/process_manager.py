from typing import List, Optional

from facefusion import store_creator
from facefusion.session_context import get_session_id, resolve_local_id
from facefusion.session_manager import resolve_owner_id
from facefusion.types import Process, ProcessState, Progress, SessionId, Stage, StageType, Store

PROCESS_STORE : Store = store_creator.create_store(
{
	'status': 'pending',
	'stages': []
})


def init() -> None:
	session_id = get_session_id()
	store_creator.init_content(PROCESS_STORE, session_id)


def get_status(session_id : SessionId) -> Optional[ProcessState]:
	if store_creator.has_content(PROCESS_STORE, session_id):
		return store_creator.get_content(PROCESS_STORE, session_id).get('status')

	return None


def get_stages() -> List[Stage]:
	session_id = get_session_id()

	if store_creator.has_content(PROCESS_STORE, session_id):
		return store_creator.get_content(PROCESS_STORE, session_id).get('stages')

	return []


def get_state() -> Optional[ProcessState]:
	session_id = get_session_id()
	owner_id = resolve_owner_id()
	local_id = resolve_local_id()

	if get_status(owner_id) == 'stopping' or get_status(local_id) == 'stopping':
		return 'stopping'

	return get_status(session_id)


def is_checking() -> bool:
	return get_state() == 'checking'


def is_processing() -> bool:
	return get_state() == 'processing'


def is_stopping() -> bool:
	return get_state() == 'stopping'


def is_pending() -> bool:
	return get_state() == 'pending'


def set_state(process_state : ProcessState) -> None:
	session_id = get_session_id()

	if store_creator.has_content(PROCESS_STORE, session_id):
		process : Process = store_creator.get_content(PROCESS_STORE, session_id)
		process['status'] = process_state


def check() -> None:
	set_state('checking')


def start() -> None:
	init()
	set_state('processing')


def stop() -> None:
	set_state('stopping')


def end() -> None:
	set_state('pending')


def stage(stage_type : StageType, title : str, progress : Optional[Progress] = None) -> None:
	next_stage : Stage =\
	{
		'type': stage_type,
		'title': title
	}

	if progress:
		next_stage['progress'] = progress.copy()

	get_stages().append(next_stage)


def update() -> None:
	stages = get_stages()

	if stages and 'progress' in stages[-1]:
		stages[-1]['progress']['current'] += 1


def seek(current : int) -> None:
	stages = get_stages()

	if stages and 'progress' in stages[-1]:
		stages[-1]['progress']['current'] = current


def clear() -> None:
	session_id = get_session_id()
	store_creator.init_content(PROCESS_STORE, session_id)


def destroy(session_id : SessionId) -> None:
	store_creator.delete_content(PROCESS_STORE, session_id)
