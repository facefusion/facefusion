import time
from contextlib import contextmanager
from typing import Iterator, List, Optional, Sized

from facefusion import stage_context, store_creator
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


def has_process(session_id : SessionId) -> bool:
	return store_creator.has_content(PROCESS_STORE, session_id)


def get_process(session_id : SessionId) -> Process:
	return store_creator.get_content(PROCESS_STORE, session_id)


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


@contextmanager
def stage(stage_type : StageType, stage_title : str, progress : Progress) -> Iterator[None]:
	next_stage : Stage =\
	{
		'type': stage_type,
		'title': stage_title,
		'progress': progress
	}

	get_stages().append(next_stage)
	stage_token = stage_context.set_stage(next_stage)

	yield

	stage_context.reset_stage(stage_token)


def count(collection : Sized) -> None:
	current_stage = stage_context.get_stage()

	if current_stage:
		current_stage['progress']['total'] = len(collection)


def describe(description : str) -> None:
	current_stage = stage_context.get_stage()

	if current_stage:
		current_stage['progress']['description'] = description


def update() -> None:
	current_stage = stage_context.get_stage()

	if current_stage:
		current_stage['progress']['current'] += 1
		current_stage['progress']['updated_at'] = time.monotonic()


def seek(current : int) -> None:
	current_stage = stage_context.get_stage()

	if current_stage:
		current_stage['progress']['current'] = current
		current_stage['progress']['updated_at'] = time.monotonic()


def clear() -> None:
	session_id = get_session_id()
	store_creator.init_content(PROCESS_STORE, session_id)


def destroy(session_id : SessionId) -> None:
	store_creator.delete_content(PROCESS_STORE, session_id)
