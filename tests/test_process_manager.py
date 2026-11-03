from typing import Iterator

import pytest

from facefusion import session_context, session_manager, store_creator
from facefusion.process_manager import PROCESS_STORE, clear, describe, destroy, end, get_state, init, is_checking, is_pending, is_processing, is_stopping, resolve_stage, seek, stage, start, stop, update
from facefusion.types import Progress


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = session_context.resolve_local_id()

	session_context.set_session_id(local_id)
	clear()
	session_context.set_session_id('session-a')
	clear()
	session_context.set_session_id('session-b')
	clear()
	session_context.set_session_id('session-a')

	yield

	session_context.set_session_id(local_id)


def test_init() -> None:
	start()
	init()

	assert store_creator.get_content(PROCESS_STORE, 'session-a') == {}


def test_start() -> None:
	process_id = start()

	assert store_creator.get_content(PROCESS_STORE, 'session-a') == { process_id: [] }
	assert get_state() == 'pending'

	session_context.set_session_id('session-b')
	start()

	assert len(store_creator.get_content(PROCESS_STORE, 'session-a')) == 1
	assert len(store_creator.get_content(PROCESS_STORE, 'session-b')) == 1


def test_get_state() -> None:
	assert get_state() == 'pending'

	start()
	stage('download', 'downloading',
	{
		'unit': 'download',
		'current': 0
	})

	assert get_state() == 'checking'

	stage('infer', 'processing',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})

	assert get_state() == 'processing'

	fork_id = session_manager.fork_session()

	assert get_state() == 'processing'

	stage('merge', 'merging',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})

	assert resolve_stage('session-a').get('type') == 'merge'

	session_context.set_session_id('session-a')
	stop()
	session_context.set_session_id(fork_id)

	assert get_state() == 'stopping'

	session_context.set_session_id('session-b')

	assert get_state() == 'pending'

	local_id = session_context.resolve_local_id()
	session_context.set_session_id(local_id)
	start()
	stage('serve', 'serving',
	{
		'unit': 'indeterminate'
	})
	stop()
	session_context.set_session_id('session-b')

	assert get_state() == 'stopping'

	session_context.set_session_id(fork_id)
	session_manager.join_session()


def test_is_pending() -> None:
	assert is_pending() is True


def test_is_checking() -> None:
	start()
	stage('download', 'downloading',
	{
		'unit': 'download',
		'current': 0
	})

	assert is_checking() is True


def test_is_processing() -> None:
	start()
	stage('infer', 'processing',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})

	assert is_processing() is True


def test_is_stopping() -> None:
	start()
	stage('infer', 'processing',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})
	stop()

	assert is_stopping() is True


def test_stop() -> None:
	stop()

	assert get_state() == 'pending'

	start()
	stop()

	assert get_state() == 'pending'

	stage('extract', 'extracting',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})
	stop()

	assert get_state() == 'stopping'
	assert resolve_stage('session-a').get('state') == 'stopping'


def test_end() -> None:
	end()

	assert store_creator.get_content(PROCESS_STORE, 'session-a') == {}

	start()
	stage('extract', 'extracting',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})
	stop()
	end()

	assert store_creator.get_content(PROCESS_STORE, 'session-a') == {}
	assert get_state() == 'pending'


def test_stage() -> None:
	stage('extract', 'extracting',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})

	assert resolve_stage('session-a') is None

	process_id = start()
	progress : Progress =\
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	}
	stage('extract', 'extracting', progress)
	progress['current'] = 10

	assert resolve_stage('session-a').get('type') == 'extract'
	assert resolve_stage('session-a').get('title') == 'extracting'
	assert resolve_stage('session-a').get('state') == 'processing'
	assert resolve_stage('session-a').get('progress').get('current') == 0

	stage('download', 'downloading',
	{
		'unit': 'download',
		'current': 0
	})

	assert resolve_stage('session-a').get('state') == 'checking'

	stage('check', 'checking',
	{
		'unit': 'indeterminate'
	})

	assert resolve_stage('session-a').get('state') == 'processing'

	stop()
	stage('merge', 'merging',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})

	assert store_creator.get_content(PROCESS_STORE, 'session-a').get(process_id)[0].get('state') == 'processing'
	assert resolve_stage('session-a').get('state') == 'stopping'

	stage('finalize', 'finalizing',
	{
		'unit': 'indeterminate'
	})

	assert store_creator.get_content(PROCESS_STORE, 'session-a').get(process_id)[0].get('progress').get('current') == 270
	assert store_creator.get_content(PROCESS_STORE, 'session-a').get(process_id)[3].get('progress').get('current') == 0
	assert resolve_stage('session-a').get('state') == 'stopping'


def test_resolve_stage() -> None:
	assert resolve_stage('session-a') is None

	start()

	assert resolve_stage('session-a') is None

	stage('extract', 'extracting',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})

	assert resolve_stage('session-a').get('type') == 'extract'
	assert resolve_stage('session-b') is None


def test_describe() -> None:
	start()
	stage('analyse', 'analysing',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})
	describe('rate = 0.0')

	assert resolve_stage('session-a').get('description') == 'rate = 0.0'


def test_update() -> None:
	start()
	stage('infer', 'processing',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})
	update()
	update()

	assert resolve_stage('session-a').get('progress').get('current') == 2


def test_seek() -> None:
	start()
	stage('extract', 'extracting',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})
	seek(135)

	assert resolve_stage('session-a').get('progress').get('current') == 135


def test_clear() -> None:
	start()
	clear()

	assert store_creator.get_content(PROCESS_STORE, 'session-a') == {}


def test_destroy() -> None:
	start()
	destroy('session-a')

	assert store_creator.has_content(PROCESS_STORE, 'session-a') is False
