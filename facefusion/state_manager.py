from typing import Union, Any
import inspect

from facefusion.typing import State, StateSet, StateContext, StateKey
from facefusion.processors.frame.typing import FrameProcessorState, FrameProcessorStateKey

STATES : Union[StateSet, FrameProcessorState] =\
{
	'core': {}, #type:ignore[typeddict-item]
	'uis': {} #type:ignore[typeddict-item]
}
UnionState = Union[State, FrameProcessorState]
UnionStateKey = Union[StateKey, FrameProcessorStateKey]


def get_state() -> UnionState:
	state_context = detect_state_context()
	return STATES.get(state_context) #type:ignore


def init_item(key : UnionStateKey, value : Any) -> None:
	STATES['core'][key] = value #type:ignore
	STATES['uis'][key] = value #type:ignore


def get_item(key : UnionStateKey) -> Any:
	return get_state().get(key) #type:ignore


def set_item(key : UnionStateKey, value : Any) -> None:
	state_context = detect_state_context()
	STATES[state_context][key] = value #type:ignore


def clear_item(key : UnionStateKey) -> None:
	set_item(key, None)


def detect_state_context() -> StateContext:
	for stack in inspect.stack():
		if 'facefusion/uis' in stack.filename:
			return 'uis'
	return 'core'
