import os
from typing import Iterator

import pytest

from facefusion import store_creator
from facefusion.session_context import resolve_local_id, set_session_id
from facefusion.session_manager import clear_api_session, create_api_session, fork_session, join_session, set_api_session
from facefusion.state_manager import STATE_SET, clear, clear_item, clone_state, collect_state, destroy, get_item, get_jobs_path, get_state, get_temp_path, init, init_item, set_item, set_state


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

	assert get_state() == { 'video_memory_strategy': 'tolerant' }

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

	set_session_id('session-a')
	set_state({ 'video_memory_strategy': 'tolerant' }) #type:ignore[arg-type]

	assert get_state() == { 'video_memory_strategy': 'tolerant' }

	set_session_id(resolve_local_id())

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
	set_session_id('session-a')
	init()
	clear()

	assert get_state() == {}

	set_session_id(resolve_local_id())

	assert get_state() == { 'video_memory_strategy': 'tolerant' }

	clear()

	assert get_state() == {}


def test_destroy() -> None:
	init_item('video_memory_strategy', 'tolerant')
	set_session_id('session-a')
	init()
	set_session_id(resolve_local_id())
	destroy('session-a')

	assert store_creator.has_content(STATE_SET, 'session-a') is False
	assert get_state() == { 'video_memory_strategy': 'tolerant' }

	destroy('session-a')

	assert store_creator.has_content(STATE_SET, 'session-a') is False


def test_collect_state() -> None:
	init_item('temp_path', '.temp')
	init_item('video_memory_strategy', 'tolerant')

	assert collect_state({ 'temp_path': 'invalid', 'jobs_path': 'invalid' }) ==\
	{
		'temp_path': '.temp',
		'jobs_path': None
	}


def test_init_item() -> None:
	init_item('video_memory_strategy', 'tolerant')

	assert get_state().get('video_memory_strategy') == 'tolerant'

	init_item('video_memory_strategy', 'strict')

	assert get_state().get('video_memory_strategy') == 'strict'


def test_get_item_and_set_item() -> None:
	set_item('video_memory_strategy', 'tolerant')

	assert get_item('video_memory_strategy') == 'tolerant'

	set_session_id('session-a')
	init()
	set_item('video_memory_strategy', 'strict')

	assert get_item('video_memory_strategy') == 'strict'

	set_session_id(resolve_local_id())

	assert get_item('video_memory_strategy') == 'tolerant'


def test_clear_item() -> None:
	init_item('video_memory_strategy', 'tolerant')
	clear_item('video_memory_strategy')

	assert get_state() == { 'video_memory_strategy': None }


def test_get_jobs_path() -> None:
	local_id = resolve_local_id()
	init_item('jobs_path', '.jobs')

	assert get_jobs_path() == os.path.join('.jobs', local_id)

	fork_id = fork_session()
	clone_state()

	assert get_jobs_path() == os.path.join('.jobs', local_id)

	join_session()
	store_creator.delete_content(STATE_SET, fork_id)
	set_api_session('session-a', create_api_session())
	set_session_id('session-a')
	init()

	assert get_jobs_path() == os.path.join('.jobs', 'session-a')

	fork_id = fork_session()
	clone_state()

	assert get_jobs_path() == os.path.join('.jobs', 'session-a')

	join_session()
	store_creator.delete_content(STATE_SET, fork_id)
	clear_api_session('session-a')


def test_get_temp_path() -> None:
	local_id = resolve_local_id()
	init_item('temp_path', '.temp')

	assert get_temp_path() == os.path.join('.temp', local_id)

	fork_id = fork_session()
	clone_state()

	assert get_temp_path() == os.path.join('.temp', local_id)

	join_session()
	store_creator.delete_content(STATE_SET, fork_id)
	set_api_session('session-a', create_api_session())
	set_session_id('session-a')
	init()

	assert get_temp_path() == os.path.join('.temp', 'session-a')

	fork_id = fork_session()
	clone_state()

	assert get_temp_path() == os.path.join('.temp', 'session-a')

	join_session()
	store_creator.delete_content(STATE_SET, fork_id)
	clear_api_session('session-a')
