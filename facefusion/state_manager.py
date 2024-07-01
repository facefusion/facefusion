from typing import Any, Union
import inspect

from facefusion.typing import State, StateSet, StateContext, StateKey
from facefusion.processors.frame.typing import FrameProcessorState, FrameProcessorStateKey

STATES : Union[StateSet, FrameProcessorState] =\
{
	'core': {}, #type:ignore
	'uis': {} #type:ignore
}

def get_state() -> Union[State, FrameProcessorState]:
	state_context = detect_state_context()
	return STATES[state_context] #type:ignore


def init_state_item(key : Union[StateKey, FrameProcessorStateKey], value : Any) -> None:
	STATES['core'][key] = value #type:ignore
	STATES['uis'][key] = value #type:ignore


def get_state_item(key : Union[StateKey, FrameProcessorStateKey]) -> Any:
	return get_state().get(key) #type:ignore


def set_state_item(key : Union[StateKey, FrameProcessorStateKey], value : Any) -> None:
	state_context = detect_state_context()
	STATES[state_context][key] = value #type:ignore


def clear_state_item(key : Union[StateKey, FrameProcessorStateKey]) -> None:
	set_state_item(key, None)


def detect_state_context() -> StateContext:
	for frame in inspect.stack():
		if 'facefusion/uis' in frame.filename:
			return 'uis'
	return 'core'
