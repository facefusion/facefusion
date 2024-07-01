from typing import Any, Union
import inspect

from facefusion.typing import State, StateSet, StateContext, StateKey
from facefusion.processors.frame.typing import FrameProcessorState, FrameProcessorStateKey

STATE : Union[StateSet, FrameProcessorState] =\
{
	'core': {}, #type:ignore
	'uis': {} #type:ignore
}


def init_state(state : Union[State, FrameProcessorState]) -> None:
	global STATE

	STATE['core'] = state #type:ignore
	STATE['uis'] = state #type:ignore


def get_state() -> Union[State, FrameProcessorState]:
	state_context = detect_state_context()
	return STATE[state_context] #type:ignore


def init_state_item(key : Union[StateKey, FrameProcessorStateKey], value : Any) -> None:
	STATE['core'][key] = value #type:ignore
	STATE['uis'][key] = value #type:ignore


def get_state_item(key : Union[StateKey, FrameProcessorStateKey]) -> Any:
	return get_state().get(key) #type:ignore


def set_state_item(key : Union[StateKey, FrameProcessorStateKey], value : Any) -> None:
	state_context = detect_state_context()
	STATE[state_context][key] = value #type:ignore


def detect_state_context() -> StateContext:
	for frame in inspect.stack():
		if 'facefusion/uis' in frame.filename:
			return 'uis'
	return 'core'
