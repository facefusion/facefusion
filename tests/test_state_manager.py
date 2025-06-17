from typing import Union

import pytest

from facefusion.processors.types import ProcessorState
from facefusion.state_manager import STATE_SET, get_item, init_item, set_item
from facefusion.types import AppContext, State


def get_state(app_context : AppContext) -> Union[State, ProcessorState]:
	return STATE_SET.get(app_context)


def clear_state(app_context : AppContext) -> None:
	STATE_SET[app_context] = {} #type:ignore[typeddict-item]


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_state('cli')
	clear_state('ui')


def test_init_item() -> None:
	init_item('video_memory_strategy', 'tolerant')

	assert get_state('cli').get('video_memory_strategy') == 'tolerant'
	assert get_state('ui').get('video_memory_strategy') == 'tolerant'


def test_get_item_and_set_item() -> None:
	set_item('video_memory_strategy', 'tolerant')

	assert get_item('video_memory_strategy') == 'tolerant'
	assert get_state('ui').get('video_memory_strategy') is None
