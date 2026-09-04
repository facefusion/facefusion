from typing import Iterator, Union

import pytest

from facefusion.processors.types import ProcessorState
from facefusion.session_context import set_session_id
from facefusion.state_manager import STATE_SET, clear_state, get_item, get_state, init_item, init_state, set_item
from facefusion.types import AppContext, SessionId, State


def get_session_state(app_context : AppContext, session_id : SessionId) -> Union[State, ProcessorState]:
	return STATE_SET.get(app_context).get(session_id)


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	yield

	set_session_id('test')


def test_init_state() -> None:
	set_session_id('session-a')
	init_state('session-a')

	assert get_session_state('cli', 'session-a') == {}


def test_get_state() -> None:
	set_session_id('session-a')
	init_state('session-a')
	set_item('video_memory_strategy', 'tolerant')

	assert get_state('session-a').get('video_memory_strategy') == 'tolerant'
	assert get_session_state('cli', 'session-a').get('video_memory_strategy') == 'tolerant'


def test_init_item() -> None:
	set_session_id('session-a')
	init_state('session-a')
	init_item('video_memory_strategy', 'tolerant')

	assert get_session_state('cli', 'session-a').get('video_memory_strategy') == 'tolerant'


def test_get_item_and_set_item() -> None:
	set_session_id('session-a')
	init_state('session-a')
	set_item('video_memory_strategy', 'tolerant')
	set_session_id('session-b')
	init_state('session-b')
	set_item('video_memory_strategy', 'strict')

	assert get_item('video_memory_strategy') == 'strict'

	set_session_id('session-a')

	assert get_item('video_memory_strategy') == 'tolerant'


def test_clear_state() -> None:
	set_session_id('session-a')
	init_state('session-a')
	set_item('video_memory_strategy', 'tolerant')
	clear_state('session-a')

	assert get_session_state('cli', 'session-a') is None
