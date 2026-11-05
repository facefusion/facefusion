from typing import Iterator
from unittest.mock import patch

import pytest

from facefusion import session_context, session_manager, store_creator
from facefusion.process_manager import PROCESS_STORE, clear, count, destroy, end, get_stages, get_state, get_status, init, is_pending, is_processing, is_stopping, seek, set_state, stage, start, stop, update


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
	set_state('processing')
	init()

	assert get_state() == 'pending'


def test_get_status() -> None:
	set_state('processing')

	assert get_status('session-a') == 'processing'
	assert get_status('session-c') is None


def test_get_stages() -> None:
	start()
	stage('extract', 'extracting',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270,
		'started_at': 10.0,
		'updated_at': 10.0
	})

	assert get_stages() ==\
	[
		{
			'type': 'extract',
			'title': 'extracting',
			'progress':
			{
				'unit': 'frame',
				'current': 0,
				'total': 270,
				'started_at': 10.0,
				'updated_at': 10.0
			}
		}
	]

	destroy('session-a')

	assert get_stages() == []


def test_get_state() -> None:
	session_context.set_session_id('session-c')

	assert get_state() is None

	session_context.set_session_id('session-a')
	set_state('processing')
	session_context.set_session_id('session-b')
	set_state('stopping')

	assert get_state() == 'stopping'

	session_context.set_session_id('session-a')

	assert get_state() == 'processing'

	fork_id = session_manager.fork_session()
	clear()

	assert get_state() == 'pending'

	set_state('processing')

	assert get_state() == 'processing'

	session_context.set_session_id('session-a')
	set_state('stopping')
	session_context.set_session_id(fork_id)

	assert get_state() == 'stopping'

	session_context.set_session_id('session-a')
	set_state('processing')
	session_context.set_session_id(fork_id)

	assert get_state() == 'processing'

	local_id = session_context.resolve_local_id()
	session_context.set_session_id(local_id)
	set_state('stopping')
	session_context.set_session_id(fork_id)

	assert get_state() == 'stopping'

	session_context.set_session_id('session-b')

	assert get_state() == 'stopping'

	session_context.set_session_id(fork_id)
	session_manager.join_session()


def test_start() -> None:
	set_state('pending')
	start()

	assert is_processing()


def test_stop_process() -> None:
	set_state('processing')
	stop()

	assert is_stopping()


def test_end_process() -> None:
	set_state('processing')
	end()

	assert is_pending()

	session_context.set_session_id('session-c')
	start()
	destroy('session-c')
	end()

	assert store_creator.has_content(PROCESS_STORE, 'session-c') is False

	session_context.set_session_id('session-a')


def test_stage() -> None:
	start()
	stage('download', 'downloading',
	{
		'unit': 'download',
		'current': 1024,
		'total': 2048,
		'started_at': 10.0,
		'updated_at': 10.0
	})
	stage('extract', 'extracting',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270,
		'started_at': 10.0,
		'updated_at': 10.0
	})

	assert get_stages() ==\
	[
		{
			'type': 'download',
			'title': 'downloading',
			'progress':
			{
				'unit': 'download',
				'current': 1024,
				'total': 2048,
				'started_at': 10.0,
				'updated_at': 10.0
			}
		},
		{
			'type': 'extract',
			'title': 'extracting',
			'progress':
			{
				'unit': 'frame',
				'current': 0,
				'total': 270,
				'started_at': 10.0,
				'updated_at': 10.0
			}
		}
	]


def test_count() -> None:
	start()
	count([ 0, 1, 2 ])

	assert get_stages() == []

	stage('infer', 'processing',
	{
		'unit': 'frame',
		'current': 0,
		'started_at': 10.0,
		'updated_at': 10.0
	})
	count([ 0, 1, 2 ])

	assert get_stages()[-1].get('progress').get('total') == 3


def test_update() -> None:
	start()
	update()

	assert get_stages() == []

	stage('infer', 'processing',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270,
		'started_at': 10.0,
		'updated_at': 10.0
	})
	update()

	with patch('time.monotonic', return_value = 20.0):
		update()

	assert get_stages()[-1].get('progress').get('current') == 2
	assert get_stages()[-1].get('progress').get('updated_at') == 20.0


def test_seek() -> None:
	start()
	stage('extract', 'extracting',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270,
		'started_at': 10.0,
		'updated_at': 10.0
	})

	with patch('time.monotonic', return_value = 20.0):
		seek(135)

	assert get_stages()[-1].get('progress').get('current') == 135
	assert get_stages()[-1].get('progress').get('updated_at') == 20.0


def test_clear() -> None:
	set_state('processing')
	clear()

	assert get_state() == 'pending'
