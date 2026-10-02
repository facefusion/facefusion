import threading
from datetime import datetime, timedelta
from functools import partial
from typing import Iterator, List

import pytest

from facefusion import content_store, face_store, inference_manager, process_manager, rtc_store, state_manager, store_creator, video_manager
from facefusion.apis import asset_store, websocket_store
from facefusion.download import conditional_download
from facefusion.session_context import resolve_local_id, set_session_id
from facefusion.session_manager import clear_api_session, clear_cli_session, create_api_session, fork_session, set_api_session
from facefusion.store_manager import conditional_api_destroy, conditional_cli_destroy, destroy, get_stores, observe_api_session, observe_cli_session
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])

	state_manager.init()


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = resolve_local_id()

	set_session_id(local_id)

	yield

	set_session_id(local_id)


def join_observe_threads(threads : List[threading.Thread], timeout : float) -> None:
	for thread in threading.enumerate():
		if thread not in threads:
			thread.join(timeout = timeout)


def test_get_stores() -> None:
	assert get_stores() == [ state_manager, asset_store, content_store, face_store, inference_manager, process_manager, rtc_store, video_manager, websocket_store ]


def test_observe_api_session() -> None:
	api_session = create_api_session()
	threads = threading.enumerate()

	set_api_session('session-a', api_session)
	set_session_id('session-a')
	state_manager.init()
	content_store.init()
	set_session_id(resolve_local_id())
	observe_api_session('session-a')
	join_observe_threads(threads, 1.5)

	assert store_creator.has_content(state_manager.STATE_SET, 'session-a') is True
	assert store_creator.has_content(content_store.CONTENT_STORE, 'session-a') is True

	api_session['expires_at'] = datetime.now() - timedelta(hours = 1)
	join_observe_threads(threads, 3.0)

	assert store_creator.has_content(state_manager.STATE_SET, 'session-a') is False
	assert store_creator.has_content(content_store.CONTENT_STORE, 'session-a') is False

	clear_api_session('session-a')


def test_observe_cli_session() -> None:
	threads = threading.enumerate()

	set_api_session('session-a', create_api_session())
	set_session_id('session-a')
	fork_id = fork_session()
	state_manager.init()
	content_store.init()
	set_session_id(resolve_local_id())
	observe_cli_session(fork_id)
	join_observe_threads(threads, 1.5)

	assert store_creator.has_content(state_manager.STATE_SET, fork_id) is True
	assert store_creator.has_content(content_store.CONTENT_STORE, fork_id) is True

	clear_api_session('session-a')
	join_observe_threads(threads, 3.0)

	assert store_creator.has_content(state_manager.STATE_SET, fork_id) is False
	assert store_creator.has_content(content_store.CONTENT_STORE, fork_id) is False

	clear_cli_session(fork_id)


def test_conditional_api_destroy() -> None:
	api_session = create_api_session()

	set_api_session('session-a', api_session)
	set_session_id('session-a')
	state_manager.init()
	content_store.init()
	set_session_id(resolve_local_id())
	destroy_thread = threading.Thread(target = partial(conditional_api_destroy, 'session-a'), daemon = True)
	destroy_thread.start()
	destroy_thread.join(timeout = 1.5)

	assert store_creator.has_content(state_manager.STATE_SET, 'session-a') is True
	assert store_creator.has_content(content_store.CONTENT_STORE, 'session-a') is True

	api_session['expires_at'] = datetime.now() - timedelta(hours = 1)
	destroy_thread.join(timeout = 3.0)

	assert store_creator.has_content(state_manager.STATE_SET, 'session-a') is False
	assert store_creator.has_content(content_store.CONTENT_STORE, 'session-a') is False
	assert store_creator.has_content(state_manager.STATE_SET, resolve_local_id()) is True

	clear_api_session('session-a')


def test_conditional_cli_destroy() -> None:
	set_api_session('session-a', create_api_session())
	set_session_id('session-a')

	fork_id = fork_session()
	video_manager.init()
	video_reader = video_manager.get_reader(get_test_example_file('target-240p.mp4'), 'read_video_frame')

	clear_api_session('session-a')
	conditional_cli_destroy(fork_id)

	assert video_reader.get('process').poll() == -9
	assert store_creator.has_content(video_manager.VIDEO_POOL_STORE, fork_id) is False

	clear_cli_session(fork_id)


def test_destroy() -> None:
	set_session_id('session-a')
	state_manager.init()
	content_store.init()
	set_session_id(resolve_local_id())
	destroy('session-a')

	assert store_creator.has_content(state_manager.STATE_SET, 'session-a') is False
	assert store_creator.has_content(content_store.CONTENT_STORE, 'session-a') is False
	assert store_creator.has_content(state_manager.STATE_SET, resolve_local_id()) is True
