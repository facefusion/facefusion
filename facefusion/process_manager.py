import secrets
from datetime import datetime
from typing import Optional

from facefusion import store_creator
from facefusion.session_context import get_session_id, resolve_local_id
from facefusion.session_manager import resolve_owner_id
from facefusion.types import ProcessId, ProcessState, Progress, SessionId, Stage, StageState, StageType, Store

PROCESS_STORE : Store = store_creator.create_store({})


def init() -> None:
	session_id = get_session_id()
	store_creator.init_content(PROCESS_STORE, session_id)


def start() -> ProcessId:
	owner_id = resolve_owner_id()
	process_id = secrets.token_urlsafe(16)
	store_creator.get_content(PROCESS_STORE, owner_id)[process_id] = []
	return process_id


def get_state() -> ProcessState:
	owner_id = resolve_owner_id()
	local_id = resolve_local_id()
	owner_stage = resolve_stage(owner_id)
	local_stage = resolve_stage(local_id)

	if local_stage and local_stage.get('state') == 'stopping':
		return 'stopping'

	if owner_stage:
		return owner_stage.get('state')

	return 'pending'


def is_pending() -> bool:
	return get_state() == 'pending'


def is_checking() -> bool:
	return get_state() == 'checking'


def is_processing() -> bool:
	return get_state() == 'processing'


def is_stopping() -> bool:
	return get_state() == 'stopping'


def stop() -> None:
	owner_id = resolve_owner_id()
	stage = resolve_stage(owner_id)

	if stage:
		stage['state'] = 'stopping'
		stage['updated_at'] = datetime.now()


def end() -> None:
	owner_id = resolve_owner_id()
	process_set = store_creator.get_content(PROCESS_STORE, owner_id)

	if process_set:
		process_id = list(process_set.keys())[-1]
		del process_set[process_id]


def stage(stage_type : StageType, title : str, progress : Progress) -> None:
	owner_id = resolve_owner_id()
	process_set = store_creator.get_content(PROCESS_STORE, owner_id)
	last_stage = resolve_stage(owner_id)
	stage_state : StageState = 'processing'

	if stage_type == 'download':
		stage_state = 'checking'

	if is_stopping():
		stage_state = 'stopping'

	if last_stage and last_stage.get('state') in [ 'checking', 'processing' ] and 'total' in last_stage.get('progress'):
		last_stage['progress']['current'] = last_stage.get('progress').get('total')
		last_stage['updated_at'] = datetime.now()

	if process_set:
		list(process_set.values())[-1].append(
		{
			'type': stage_type,
			'state': stage_state,
			'title': title,
			'progress': progress.copy(),
			'created_at': datetime.now(),
			'updated_at': datetime.now()
		})


def resolve_stage(session_id : SessionId) -> Optional[Stage]:
	process_set = store_creator.get_content(PROCESS_STORE, session_id)

	if process_set:
		stages = list(process_set.values())[-1]

		if stages:
			return stages[-1]

	return None


def describe(description : str) -> None:
	owner_id = resolve_owner_id()
	stage = resolve_stage(owner_id)

	if stage:
		stage['description'] = description


def update() -> None:
	owner_id = resolve_owner_id()
	stage = resolve_stage(owner_id)

	if stage:
		seek(stage.get('progress').get('current') + 1)


def seek(current : int) -> None:
	owner_id = resolve_owner_id()
	stage = resolve_stage(owner_id)

	if stage:
		stage['progress']['current'] = current
		stage['updated_at'] = datetime.now()


def clear() -> None:
	session_id = get_session_id()
	store_creator.init_content(PROCESS_STORE, session_id)


def destroy(session_id : SessionId) -> None:
	store_creator.delete_content(PROCESS_STORE, session_id)
