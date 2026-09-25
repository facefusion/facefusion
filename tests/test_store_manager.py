from typing import Iterator

import pytest

from facefusion import state_manager, store_creator, video_manager
from facefusion.download import conditional_download
from facefusion.session_context import resolve_local_id, set_session_id
from facefusion.session_manager import clear_api_session, clear_cli_session, create_api_session, fork_session, set_api_session
from facefusion.store_manager import conditional_cli_destroy
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
