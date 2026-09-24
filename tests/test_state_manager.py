from typing import Iterator

import pytest

from facefusion import store_creator
from facefusion.session_context import resolve_local_id, set_session_id
from facefusion.session_manager import fork_session, join_session
from facefusion.state_manager import STATE_SET, clear, clone_state, get_item, get_state, init, init_item, set_item, set_state


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = resolve_local_id()

	set_session_id(local_id)
	clear()
	store_creator.delete_content(STATE_SET, 'session-a')
	store_creator.delete_content(STATE_SET, 'session-a1')

	yield

	set_session_id(local_id)


def test_init() -> None:
	init_item('video_memory_strategy', 'tolerant')
	set_session_id('session-a')

	assert get_state() is None

	init()
	set_item('video_memory_strategy', 'strict')

	assert get_state() == { 'video_memory_strategy': 'strict' }

	set_session_id(resolve_local_id())

	assert get_state() == { 'video_memory_strategy': 'tolerant' }


def test_get_state() -> None:
	init_item('video_memory_strategy', 'tolerant')

	assert get_state() == { 'video_memory_strategy': 'tolerant' }


def test_set_state() -> None:
	set_state({ 'video_memory_strategy': 'strict' }) #type:ignore[arg-type]

	assert get_state() == { 'video_memory_strategy': 'strict' }


def test_clone_state() -> None:
	init_item('video_memory_strategy', 'tolerant')
	fork_id = fork_session()
	clone_state()
	set_item('video_memory_strategy', 'strict')

	assert get_state() == { 'video_memory_strategy': 'strict' }

	join_session()

	assert get_state() == { 'video_memory_strategy': 'tolerant' }

	store_creator.delete_content(STATE_SET, fork_id)


def test_clear() -> None:
	init_item('video_memory_strategy', 'tolerant')
	clear()

	assert get_state() == {}


def test_init_item() -> None:
	init_item('video_memory_strategy', 'tolerant')

	assert get_state().get('video_memory_strategy') == 'tolerant'


def test_get_item_and_set_item() -> None:
	set_item('video_memory_strategy', 'tolerant')

	assert get_item('video_memory_strategy') == 'tolerant'
