from datetime import datetime, timedelta

from _pytest.capture import CaptureFixture

from facefusion.cli_progress import RENDER_SET, format_progress, queue_log, render_progresses, resolve_count, resolve_download, resolve_fill, resolve_frame, resolve_percent, resolve_rate, resolve_rate_label
from facefusion.types import Task


def test_queue_log() -> None:
	queue_log('[FACEFUSION.CORE] processing step 1 of 1')

	assert RENDER_SET.get('log_messages')[-1] == '[FACEFUSION.CORE] processing step 1 of 1'

	RENDER_SET.get('log_messages').clear()


def test_render_progresses(capsys : CaptureFixture[str]) -> None:
	RENDER_SET['rendered_at'] = datetime.now() - timedelta(seconds = 1)
	capsys.readouterr()
	render_progresses(
	[
		{
			'id': 'extract',
			'type': 'extract',
			'state': 'pending',
			'title': 'extracting',
			'progress':
			{
				'unit': 'frame',
				'current': 270,
				'total': 270
			},
			'created_at': datetime.now() - timedelta(seconds = 10),
			'updated_at': datetime.now()
		},
		{
			'id': 'stream',
			'type': 'stream',
			'state': 'processing',
			'title': 'streaming',
			'progress':
			{
				'unit': 'frame',
				'current': 841
			},
			'created_at': datetime.now() - timedelta(seconds = 10),
			'updated_at': datetime.now()
		}
	])
	output = capsys.readouterr().out

	assert output.startswith('extracting')
	assert len(output.splitlines()) == 1


def test_format_progress() -> None:
	task : Task =\
	{
		'id': 'analyse',
		'type': 'analyse',
		'state': 'processing',
		'title': 'analysing',
		'description': 'rate = 0.0',
		'progress':
		{
			'unit': 'frame',
			'current': 135,
			'total': 270
		},
		'created_at': datetime.now() - timedelta(seconds = 10),
		'updated_at': datetime.now()
	}

	assert format_progress(task).startswith('analysing')
	assert '135 / 270' in format_progress(task)
	assert '13.5 frame/s' in format_progress(task)

	task['state'] = 'stopping'

	assert format_progress(task).startswith('stopping')


def test_resolve_fill() -> None:
	task : Task =\
	{
		'id': 'extract',
		'type': 'extract',
		'state': 'processing',
		'title': 'extracting',
		'progress':
		{
			'unit': 'frame',
			'current': 135,
			'total': 270
		},
		'created_at': datetime.now() - timedelta(seconds = 3),
		'updated_at': datetime.now()
	}

	assert resolve_fill(task, 40) == 20

	task['progress']['total'] = 0

	assert resolve_fill(task, 40) == 0

	del task['progress']['total']

	assert resolve_fill(task, 40) in range(15, 25)


def test_resolve_count() -> None:
	task : Task =\
	{
		'id': 'infer',
		'type': 'infer',
		'state': 'processing',
		'title': 'processing',
		'progress':
		{
			'unit': 'frame',
			'current': 84,
			'total': 120
		},
		'created_at': datetime.now(),
		'updated_at': datetime.now()
	}

	assert resolve_count(task) == '84 / 120'

	task['progress']['unit'] = 'percent'

	assert resolve_count(task) == '70 %'

	del task['progress']['total']

	assert resolve_count(task) == '84'


def test_resolve_rate_label() -> None:
	task : Task =\
	{
		'id': 'upload',
		'type': 'upload',
		'state': 'processing',
		'title': 'uploading',
		'progress':
		{
			'unit': 'percent',
			'current': 50,
			'total': 100
		},
		'created_at': datetime.now() - timedelta(seconds = 10),
		'updated_at': datetime.now()
	}

	assert resolve_rate_label(task) == ''

	task['progress']['unit'] = 'frame'

	assert resolve_rate_label(task) == '5.0 frame/s'

	task['progress']['unit'] = 'download'

	assert resolve_rate_label(task) == '0.0 kb/s'


def test_resolve_rate() -> None:
	task : Task =\
	{
		'id': 'stream',
		'type': 'stream',
		'state': 'processing',
		'title': 'streaming',
		'progress':
		{
			'unit': 'frame',
			'current': 10
		},
		'created_at': datetime.now() - timedelta(seconds = 10),
		'updated_at': datetime.now()
	}

	assert round(resolve_rate(task), 1) == 1.0

	task['updated_at'] = task.get('created_at')

	assert resolve_rate(task) == 0.0


def test_resolve_percent() -> None:
	task : Task =\
	{
		'id': 'upload',
		'type': 'upload',
		'state': 'processing',
		'title': 'uploading',
		'progress':
		{
			'unit': 'percent',
			'current': 1,
			'total': 10
		},
		'created_at': datetime.now(),
		'updated_at': datetime.now()
	}

	assert resolve_percent(task) == '10 %'

	task['progress']['total'] = 0

	assert resolve_percent(task) == '0 %'


def test_resolve_frame() -> None:
	task : Task =\
	{
		'id': 'infer',
		'type': 'infer',
		'state': 'processing',
		'title': 'processing',
		'progress':
		{
			'unit': 'frame',
			'current': 10,
			'total': 100
		},
		'created_at': datetime.now() - timedelta(seconds = 10),
		'updated_at': datetime.now()
	}

	assert resolve_frame(task) == '1.0 frame/s'

	task['updated_at'] = task.get('created_at')

	assert resolve_frame(task) == '0.0 frame/s'


def test_resolve_download() -> None:
	task : Task =\
	{
		'id': 'download',
		'type': 'download',
		'state': 'checking',
		'title': 'downloading',
		'progress':
		{
			'unit': 'download',
			'current': 10 * 1024,
			'total': 20 * 1024 * 1024
		},
		'created_at': datetime.now() - timedelta(seconds = 10),
		'updated_at': datetime.now()
	}

	assert resolve_download(task) == '1.0 kb/s'

	task['progress']['current'] = 20 * 1024 * 1024

	assert resolve_download(task) == '2.0 mb/s'

	task['updated_at'] = task.get('created_at')

	assert resolve_download(task) == '0.0 kb/s'
