from typing import Any, Union

from facefusion.app_context import detect_app_context
from facefusion.processors.types import ProcessorState, ProcessorStateKey, ProcessorStateSet
from facefusion.types import Args, State, StateKey, StateSet

STATE_SET : Union[StateSet, ProcessorStateSet] =\
{
	'api': {}, #type:ignore[assignment]
	'cli': {} #type:ignore[assignment]
}


def get_state() -> Union[State, ProcessorState]:
	app_context = detect_app_context()
	return STATE_SET.get(app_context) #type:ignore[return-value]


def collect_state(args : Args) -> Union[State, ProcessorState]:
	state =\
	{
		key: get_item(key) for key in args #type:ignore[arg-type]
	}
	return state #type:ignore[return-value]


def init_item(key : Union[StateKey, ProcessorStateKey], value : Any) -> None:
	STATE_SET['api'][key] = value #type:ignore[literal-required]
	STATE_SET['cli'][key] = value #type:ignore[literal-required]


def get_item(key : Union[StateKey, ProcessorStateKey]) -> Any:
	return get_state().get(key) #type:ignore[literal-required]


def set_item(key : Union[StateKey, ProcessorStateKey], value : Any) -> None:
	app_context = detect_app_context()
	STATE_SET[app_context][key] = value #type:ignore[literal-required]


def clear_item(key : Union[StateKey, ProcessorStateKey]) -> None:
	set_item(key, None)
