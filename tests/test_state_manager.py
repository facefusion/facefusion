import os
from typing import Iterator, Union

import pytest

from facefusion.processors.types import ProcessorState
from facefusion.session_context import clear_session_id, resolve_step_id, set_session_id
from facefusion.state_manager import STATE_SET, clear_state, get_item, get_state, init_item, resolve_temp_path, set_item, set_state
from facefusion.types import SessionId, State


def get_session_state(session_id : SessionId) -> Union[State, ProcessorState]:
	return STATE_SET.get(session_id)


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	clear_session_id()

	yield

	clear_session_id()


def test_get_state() -> None:
	set_session_id('session-a')
	set_item('video_memory_strategy', 'tolerant')

	assert get_state('session-a').get('video_memory_strategy') == 'tolerant'
	assert get_session_state('session-a').get('video_memory_strategy') == 'tolerant'


def test_set_state() -> None:
	set_state('session-a', { 'video_memory_strategy': 'strict' })
	set_session_id('session-a')

	assert get_item('video_memory_strategy') == 'strict'


def test_init_item() -> None:
	set_session_id('session-a')
	init_item('video_memory_strategy', 'tolerant')

	assert get_session_state('session-a').get('video_memory_strategy') == 'tolerant'


def test_get_item_and_set_item() -> None:
	set_session_id('session-a')
	set_item('video_memory_strategy', 'tolerant')
	set_session_id('session-b')
	set_item('video_memory_strategy', 'strict')

	assert get_item('video_memory_strategy') == 'strict'

	set_session_id('session-a')

	assert get_item('video_memory_strategy') == 'tolerant'


def test_clear_state() -> None:
	set_session_id('session-a')
	set_item('video_memory_strategy', 'tolerant')
	clear_state('session-a')

	assert get_session_state('session-a') is None


def test_resolve_temp_path() -> None:
	set_session_id('session-a')
	set_item('temp_path', '/tmp')

	assert resolve_temp_path() == os.path.join('/tmp', 'session-a')

	set_session_id(resolve_step_id('session-a'))
	set_item('temp_path', '/tmp')

	assert resolve_temp_path() == os.path.join('/tmp', 'session-a')
