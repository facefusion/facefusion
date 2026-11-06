import os
import time
from unittest.mock import patch

import pytest
from _pytest.capture import CaptureFixture

from facefusion import choices, process_manager
from facefusion.cli_progress import create, render


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	process_manager.clear()


def test_update(capsys : CaptureFixture[str]) -> None:
	time_current = time.monotonic()
	process_manager.stage('download', 'downloading',
	{
		'unit': 'download',
		'current': 0,
		'total': 100,
		'started_at': time_current,
		'updated_at': time_current
	})
	process_manager.stage('extract', 'extracting',
	{
		'unit': 'frame',
		'current': 0,
		'total': 100,
		'started_at': time_current,
		'updated_at': time_current
	})

	with create() as progress:
		capsys.readouterr()
		progress.update()
		progress.update()
		output = capsys.readouterr().out

		assert output.count('extracting') == 1
		assert output.count('downloading') == 0


def test_render_percent(capsys : CaptureFixture[str]) -> None:
	time_current = time.monotonic()

	with patch('shutil.get_terminal_size', return_value = os.terminal_size((40, 20))):
		render(
		{
			'unit': 'percent',
			'current': 1,
			'total': 10,
			'started_at': time_current,
			'updated_at': time_current
		}, 'downloading')

		assert choices.progress_action_set.get('color_active') + '==' + choices.progress_action_set.get('color_neutral') + '=' * 21 + choices.progress_action_set.get('reset') + ' 10 %' in capsys.readouterr().out

	render(
	{
		'unit': 'percent',
		'current': 1,
		'total': 0,
		'started_at': time_current,
		'updated_at': time_current
	}, 'downloading')

	assert '0 %' in capsys.readouterr().out


def test_render_frame(capsys : CaptureFixture[str]) -> None:
	render(
	{
		'unit': 'frame',
		'current': 10,
		'total': 100,
		'started_at': time.monotonic() - 10,
		'updated_at': time.monotonic()
	}, 'extracting')

	assert '1.0frame/s' in capsys.readouterr().out

	render(
	{
		'unit': 'frame',
		'current': 10,
		'total': 100,
		'started_at': time.monotonic() + 10,
		'updated_at': time.monotonic()
	}, 'extracting')

	assert '0.0frame/s' in capsys.readouterr().out


def test_render_download(capsys : CaptureFixture[str]) -> None:
	render(
	{
		'unit': 'download',
		'current': 10 * 1024,
		'total': 20 * 1024 * 1024,
		'description': 'file_name = example.bin',
		'started_at': time.monotonic() - 10,
		'updated_at': time.monotonic()
	}, 'downloading')

	assert '1.0kb/s | file_name = example.bin' in capsys.readouterr().out

	render(
	{
		'unit': 'download',
		'current': 20 * 1024 * 1024,
		'total': 20 * 1024 * 1024,
		'started_at': time.monotonic() - 10,
		'updated_at': time.monotonic()
	}, 'downloading')

	assert '2.0mb/s' in capsys.readouterr().out

	render(
	{
		'unit': 'download',
		'current': 10 * 1024,
		'total': 20 * 1024 * 1024,
		'started_at': time.monotonic() + 10,
		'updated_at': time.monotonic()
	}, 'downloading')

	assert '0.0kb/s' in capsys.readouterr().out
