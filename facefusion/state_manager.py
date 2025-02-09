from typing import Any, Union

from facefusion.app_context import detect_app_context
from facefusion.processors.types import ProcessorState, ProcessorStateKey, ProcessorStateSet
from facefusion.types import State, StateKey, StateSet

STATE_SET : Union[StateSet, ProcessorStateSet] =\
{
	'cli': {}, #type:ignore[typeddict-item]
	'ui': {} #type:ignore[typeddict-item]
}


def get_state() -> Union[State, ProcessorState]:
	app_context = detect_app_context()
	return STATE_SET.get(app_context) #type:ignore


def init_item(key : Union[StateKey, ProcessorStateKey], value : Any) -> None:
	STATE_SET['cli'][key] = value #type:ignore
	STATE_SET['ui'][key] = value #type:ignore


def get_item(key : Union[StateKey, ProcessorStateKey]) -> Any:
	return get_state().get(key) #type:ignore


def set_item(key : Union[StateKey, ProcessorStateKey], value : Any) -> None:
	app_context = detect_app_context()
	STATE_SET[app_context][key] = value #type:ignore


def sync_item(key : Union[StateKey, ProcessorStateKey]) -> None:
	STATE_SET['cli'][key] = STATE_SET.get('ui').get(key) #type:ignore


def clear_item(key : Union[StateKey, ProcessorStateKey]) -> None:
	set_item(key, None)
