from typing import Iterator

import pytest

from facefusion import session_context, store_creator
from facefusion.process_manager import PROCESS_STORE, clear, collect_tasks, describe_task, destroy, end_process, end_task, get_process_id, get_process_set, get_process_state, get_task, get_tasks, has_running_tasks, init, is_process_checking, is_process_pending, is_process_processing, is_process_stopping, seek_task, start_process, start_task, stop_process, stop_processes, update_task


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = session_context.resolve_local_id()

	session_context.set_session_id('session-a')
	clear()
	session_context.set_session_id('session-b')
	clear()
	session_context.set_session_id('session-a')

	yield

	session_context.set_session_id(local_id)


def test_init() -> None:
	start_process()
	init()

	assert get_process_set() == {}


def test_clear() -> None:
	start_process()
	clear()

	assert get_process_set() == {}


def test_destroy() -> None:
	start_process()
	destroy('session-a')

	assert store_creator.has_content(PROCESS_STORE, 'session-a') is False


def test_start_process() -> None:
	process_id = start_process()

	assert get_process_id() == process_id
	assert get_process_set().get(process_id) == []


def test_stop_process() -> None:
	stop_process()

	assert get_process_state() == 'pending'

	start_process()
	start_task('stream', 'streaming',
	{
		'unit': 'frame',
		'current': 0
	})
	stop_process()

	assert get_process_state() == 'stopping'


def test_stop_processes() -> None:
	start_process()
	start_task('stream', 'streaming',
	{
		'unit': 'frame',
		'current': 0
	})
	session_context.set_session_id('session-b')
	start_process()
	start_task('upload', 'uploading',
	{
		'unit': 'percent',
		'current': 0,
		'total': 100
	})
	end_task()
	stop_processes()

	assert session_context.get_session_id() == 'session-b'
	assert get_process_state() == 'pending'

	session_context.set_session_id('session-a')

	assert get_process_state() == 'stopping'


def test_end_process() -> None:
	start_process()
	start_task('stream', 'streaming',
	{
		'unit': 'frame',
		'current': 0
	})
	stop_process()
	end_process()

	assert get_process_state() == 'pending'


def test_get_process_set() -> None:
	start_process()
	start_process()
	session_context.set_session_id('session-b')
	start_process()

	assert len(get_process_set()) == 1

	session_context.set_session_id('session-a')

	assert len(get_process_set()) == 2


def test_get_process_id() -> None:
	assert get_process_id() is None

	start_process()
	process_id = start_process()

	assert get_process_id() == process_id


def test_get_process_state() -> None:
	assert get_process_state() == 'pending'

	start_process()
	start_task('download', 'downloading',
	{
		'unit': 'download',
		'current': 0
	})

	assert get_process_state() == 'checking'

	start_task('infer', 'processing',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})

	assert get_process_state() == 'processing'


def test_is_process_pending() -> None:
	assert is_process_pending() is True


def test_is_process_checking() -> None:
	start_process()
	start_task('download', 'downloading',
	{
		'unit': 'download',
		'current': 0
	})

	assert is_process_checking() is True


def test_is_process_processing() -> None:
	start_process()
	start_task('infer', 'processing',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})

	assert is_process_processing() is True


def test_is_process_stopping() -> None:
	start_process()
	start_task('infer', 'processing',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})
	stop_process()

	assert is_process_stopping() is True


def test_start_task() -> None:
	start_process()
	progress =\
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	}
	task_id = start_task('extract', 'extracting', progress)
	progress['current'] = 10

	assert get_task().get('id') == task_id
	assert get_task().get('type') == 'extract'
	assert get_task().get('title') == 'extracting'
	assert get_task().get('state') == 'processing'
	assert get_task().get('progress').get('current') == 0

	stop_process()
	start_task('merge', 'merging',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})

	assert get_tasks()[0].get('state') == 'pending'
	assert get_task().get('state') == 'stopping'


def test_describe_task() -> None:
	start_process()
	start_task('analyse', 'analysing',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})
	describe_task('rate = 0.0')

	assert get_task().get('description') == 'rate = 0.0'


def test_update_task() -> None:
	start_process()
	start_task('stream', 'streaming',
	{
		'unit': 'frame',
		'current': 0
	})
	update_task()
	update_task()

	assert get_task().get('progress').get('current') == 2


def test_seek_task() -> None:
	start_process()
	start_task('extract', 'extracting',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})
	seek_task(135)

	assert get_task().get('progress').get('current') == 135


def test_end_task() -> None:
	start_process()
	start_task('extract', 'extracting',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})
	end_task()

	assert get_task().get('state') == 'pending'
	assert get_task().get('progress').get('current') == 270

	start_task('stream', 'streaming',
	{
		'unit': 'frame',
		'current': 0
	})
	seek_task(841)
	end_task()

	assert get_task().get('state') == 'pending'
	assert get_task().get('progress').get('current') == 841

	start_task('merge', 'merging',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})
	stop_process()
	end_task()

	assert get_task().get('state') == 'stopping'
	assert get_task().get('progress').get('current') == 0


def test_get_tasks() -> None:
	assert get_tasks() == []

	start_process()
	start_task('extract', 'extracting',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})
	start_task('infer', 'processing',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})

	assert len(get_tasks()) == 2


def test_get_task() -> None:
	assert get_task() is None

	start_process()
	task_id = start_task('extract', 'extracting',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})

	assert get_task().get('id') == task_id


def test_collect_tasks() -> None:
	start_process()
	stream_task_id = start_task('stream', 'streaming',
	{
		'unit': 'frame',
		'current': 0
	})
	session_context.set_session_id('session-b')
	start_process()
	infer_task_id = start_task('infer', 'processing',
	{
		'unit': 'frame',
		'current': 0,
		'total': 270
	})
	task_ids = []

	for task in collect_tasks():
		task_ids.append(task.get('id'))

	assert stream_task_id in task_ids
	assert infer_task_id in task_ids


def test_has_running_tasks() -> None:
	assert has_running_tasks() is False

	start_process()
	start_task('stream', 'streaming',
	{
		'unit': 'frame',
		'current': 0
	})

	assert has_running_tasks() is True

	end_task()

	assert has_running_tasks() is False
