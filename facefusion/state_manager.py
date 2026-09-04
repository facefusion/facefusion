import os
from typing import Union

from facefusion.app_context import detect_app_context
from facefusion.processors.types import ProcessorState, ProcessorStateKey, ProcessorStateSet
from facefusion.session_context import get_session_id
from facefusion.types import AppContext, Args, SessionId, State, StateKey, StateSet, StateValue

STATE_SET : Union[StateSet, ProcessorStateSet] =\
{
	'api': {}, #type:ignore[assignment]
	'cli': {} #type:ignore[assignment]
}


def init_state(session_id : SessionId) -> None:
	app_context = detect_app_context()
	STATE_SET[app_context][session_id] = {} #type:ignore[assignment]


def get_context_state(app_context : AppContext, session_id : SessionId) -> Union[State, ProcessorState]:
	return STATE_SET.get(app_context).get(session_id)


def get_state(session_id : SessionId) -> Union[State, ProcessorState]:
	app_context = detect_app_context()
	return get_context_state(app_context, session_id)


def set_state(session_id : SessionId, state : Union[State, ProcessorState]) -> None:
	app_context = detect_app_context()
	STATE_SET[app_context][session_id] = state #type:ignore[assignment]


def collect_state(args : Args) -> Union[State, ProcessorState]:
	state =\
	{
		key: get_item(key) for key in args
	}
	return state


def clear_state(session_id : SessionId) -> None:
	app_context = detect_app_context()

	if session_id in STATE_SET.get(app_context):
		del STATE_SET[app_context][session_id]


def init_item(key : Union[StateKey, ProcessorStateKey], value : StateValue) -> None:
	app_context = detect_app_context()
	session_id = get_session_id()
	state = STATE_SET[app_context].setdefault(session_id, {})
	state[key] = value #type:ignore[literal-required]


def get_item(key : Union[StateKey, ProcessorStateKey]) -> StateValue:
	session_id = get_session_id()
	return get_state(session_id).get(key)


def set_item(key : Union[StateKey, ProcessorStateKey], value : StateValue) -> None:
	app_context = detect_app_context()
	session_id = get_session_id()
	STATE_SET[app_context][session_id][key] = value #type:ignore[literal-required]


def clear_item(key : Union[StateKey, ProcessorStateKey]) -> None:
	set_item(key, None)


def resolve_temp_path() -> str:
	temp_path = get_item('temp_path')
	session_id = get_session_id()

	return os.path.join(temp_path, session_id)
