from typing import Any, Union

from facefusion.app_context import detect_app_context
from facefusion.processors.typing import ProcessorState, ProcessorStateKey
from facefusion.typing import State, StateKey, StateSet

STATES : Union[StateSet, ProcessorState] =\
{
	'cli': {}, #type:ignore[typeddict-item]
	'ui': {} #type:ignore[typeddict-item]
}
UnionState = Union[State, ProcessorState]
UnionStateKey = Union[StateKey, ProcessorStateKey]


def get_state() -> UnionState:
	app_context = detect_app_context()
	return STATES.get(app_context) #type:ignore


def init_item(key : UnionStateKey, value : Any) -> None:
	STATES['cli'][key] = value #type:ignore
	STATES['ui'][key] = value #type:ignore


def get_item(key : UnionStateKey) -> Any:
	return get_state().get(key) #type:ignore


def set_item(key : UnionStateKey, value : Any) -> None:
	app_context = detect_app_context()
	STATES[app_context][key] = value #type:ignore


def sync_item(key : UnionStateKey) -> None:
	STATES['cli'][key] = STATES.get('ui').get(key) #type:ignore


def clear_item(key : UnionStateKey) -> None:
	set_item(key, None)
