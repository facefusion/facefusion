import os
from copy import deepcopy
from typing import Union

from facefusion import store_creator
from facefusion.processors.types import ProcessorState, ProcessorStateKey
from facefusion.session_context import get_session_id, resolve_local_id
from facefusion.session_manager import resolve_owner_id
from facefusion.types import Args, State, StateKey, StateValue, Store

STATE_SET : Store = store_creator.create_store({})


def init() -> None:
	session_id = get_session_id()
	local_id = resolve_local_id()

	if session_id == local_id:
		store_creator.init_content(STATE_SET, session_id)
	else:
		store_creator.set_content(STATE_SET, session_id, deepcopy(store_creator.get_content(STATE_SET, local_id)))


def get_state() -> Union[State, ProcessorState]:
	session_id = get_session_id()

	return store_creator.get_content(STATE_SET, session_id)


def set_state(state : Union[State, ProcessorState]) -> None:
	session_id = get_session_id()
	store_creator.set_content(STATE_SET, session_id, state)


def clone_state() -> None:
	session_id = get_session_id()
	owner_id = resolve_owner_id()
	store_creator.set_content(STATE_SET, session_id, deepcopy(store_creator.get_content(STATE_SET, owner_id)))


def clear() -> None:
	session_id = get_session_id()
	store_creator.init_content(STATE_SET, session_id)


def collect_state(args : Args) -> Union[State, ProcessorState]:
	state =\
	{
		key: get_item(key) for key in args
	}
	return state


def init_item(key : Union[StateKey, ProcessorStateKey], value : StateValue) -> None:
	get_state()[key] = value #type:ignore[literal-required]


def get_item(key : Union[StateKey, ProcessorStateKey]) -> StateValue:
	return get_state().get(key)


def set_item(key : Union[StateKey, ProcessorStateKey], value : StateValue) -> None:
	get_state()[key] = value #type:ignore[literal-required]


def clear_item(key : Union[StateKey, ProcessorStateKey]) -> None:
	set_item(key, None)


def get_jobs_path() -> str:
	jobs_path = get_item('jobs_path')
	owner_id = resolve_owner_id()

	return os.path.join(jobs_path, owner_id)


def get_temp_path() -> str:
	temp_path = get_item('temp_path')
	owner_id = resolve_owner_id()

	return os.path.join(temp_path, owner_id)
