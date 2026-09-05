import os
from typing import Union

from facefusion.processors.types import ProcessorState, ProcessorStateKey, ProcessorStateSet
from facefusion.session_context import get_session_id, resolve_owner_id
from facefusion.types import Args, SessionId, State, StateKey, StateSet, StateValue

STATE_SET : Union[StateSet, ProcessorStateSet] = {}


def get_state(session_id : SessionId) -> Union[State, ProcessorState]:
	return STATE_SET.setdefault(session_id, {}) #type:ignore[arg-type]


def set_state(session_id : SessionId, state : Union[State, ProcessorState]) -> None:
	STATE_SET[session_id] = state #type:ignore[assignment]


def clear_state(session_id : SessionId) -> None:
	if session_id in STATE_SET:
		del STATE_SET[session_id]


def collect_state(args : Args) -> Union[State, ProcessorState]:
	state =\
	{
		key: get_item(key) for key in args
	}
	return state


def init_item(key : Union[StateKey, ProcessorStateKey], value : StateValue) -> None:
	session_id = get_session_id()
	get_state(session_id)[key] = value #type:ignore[literal-required]


def get_item(key : Union[StateKey, ProcessorStateKey]) -> StateValue:
	session_id = get_session_id()
	return get_state(session_id).get(key)


def set_item(key : Union[StateKey, ProcessorStateKey], value : StateValue) -> None:
	session_id = get_session_id()
	get_state(session_id)[key] = value #type:ignore[literal-required]


def clear_item(key : Union[StateKey, ProcessorStateKey]) -> None:
	set_item(key, None)


def resolve_temp_path() -> str:
	temp_path = get_item('temp_path')
	owner_id = resolve_owner_id()

	return os.path.join(temp_path, owner_id)
