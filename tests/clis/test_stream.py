import logging

import pytest
from _pytest.capture import CaptureFixture

from facefusion import choices, session_context, session_manager, state_manager
from facefusion.clis.stream import STREAM_LINE, clear_line, clear_progress, color_message, create_group_line, create_line, format_record, get_line_offset, resolve_group_color, resolve_line_group, write, write_progress


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_line()


def test_create_line() -> None:
	color_neutral = choices.color_palette.get('grey')
	reset = choices.color_palette.get('reset')

	assert create_line('api.1', '┬', 'core', 'message') == choices.color_palette.get('magenta') + 'api.1   ┬ ' + color_neutral + 'core          ' + reset + '  message'
	assert create_line('api.1', '│', 'core', 'message') == choices.color_palette.get('magenta') + '        │ ' + color_neutral + 'core          ' + reset + '  message'
	assert create_line('server', '▶', 'inference_manager', 'message') == color_neutral + 'server  ▶ ' + color_neutral + 'inference_manager' + reset + '  message'


def test_get_line_offset() -> None:
	assert get_line_offset() == 26


def test_resolve_group_color() -> None:
	assert resolve_group_color('api.0') == choices.color_palette.get('cyan')
	assert resolve_group_color('cli.6') == choices.color_palette.get('magenta')
	assert resolve_group_color('server') == choices.color_palette.get('grey')


def test_resolve_line_group() -> None:
	local_id = session_context.resolve_local_id()

	assert resolve_line_group() == 'cli.0'

	session_manager.set_cli_session(local_id, session_manager.create_cli_session())
	session_manager.fork_session()

	assert resolve_line_group() == 'cli.1'

	session_manager.join_session()
	session_manager.clear_cli_session(local_id)
	session_manager.set_api_session('api-session-1', session_manager.create_api_session())
	session_manager.set_api_session('api-session-2', session_manager.create_api_session())
	session_context.set_session_id('api-session-2')

	assert resolve_line_group() == 'api.1'

	session_manager.fork_session()

	assert resolve_line_group() == 'api.1'

	session_manager.join_session()
	session_context.set_session_id(local_id)
	session_manager.clear_api_session('api-session-1')
	session_manager.clear_api_session('api-session-2')
	state_manager.init_item('command', 'api')

	assert resolve_line_group() == 'server'

	state_manager.clear_item('command')


def test_create_group_line() -> None:
	assert create_group_line('server', 'uvicorn', 'started') == create_line('server', '┬', 'uvicorn', 'started')
	assert create_group_line('server', 'request', 'post /session 201') == create_line('server', '│', 'request', 'post /session 201')
	assert create_group_line('api.0', 'core', 'processing') == create_line('api.0', '┬', 'core', 'processing')

	for _ in range(18):
		create_group_line('api.0', 'core', 'processing')

	assert create_group_line('api.0', 'core', 'processing') == create_line('api.0', '│', 'core', 'processing')
	assert create_group_line('api.0', 'core', 'processing') == create_line('api.0', '┬', 'core', 'processing')


def test_format_record() -> None:
	server_record = logging.LogRecord('uvicorn.error', logging.ERROR, __file__, 0, '[Errno %d] address already in use', (98,), None)
	core_record = logging.makeLogRecord({ 'name': 'facefusion', 'msg': 'processing step 1 of 1', 'module_name': 'facefusion.core' })
	table_record = logging.makeLogRecord({ 'name': 'facefusion', 'msg': '+---+' })

	assert format_record(server_record) is True
	assert server_record.getMessage() == '[Errno 98] address already in use'
	assert format_record(core_record) is True
	assert core_record.getMessage() == create_line('cli.0', '┬', 'core', 'processing step 1 of 1')
	assert format_record(table_record) is True
	assert table_record.getMessage() == '+---+'
	assert STREAM_LINE.get('line_group') == ''


def test_color_message() -> None:
	assert color_message('message', logging.INFO) == 'message'
	assert color_message('message', logging.WARNING) == choices.color_palette.get('yellow') + 'message' + choices.color_palette.get('reset')
	assert color_message('message', logging.ERROR) == choices.color_palette.get('red') + 'message' + choices.color_palette.get('reset')


def test_write(capsys : CaptureFixture[str]) -> None:
	write('hello\n')

	assert capsys.readouterr().err == choices.progress_action_set.get('cursor_start') + choices.progress_action_set.get('erase_line') + 'hello\n'


def test_write_progress(capsys : CaptureFixture[str]) -> None:
	write_progress('progress')

	assert capsys.readouterr().err == choices.progress_action_set.get('cursor_start') + 'progress' + choices.progress_action_set.get('erase_line')


def test_clear_line() -> None:
	create_group_line('server', 'server', 'started')
	clear_line()

	assert STREAM_LINE ==\
	{
		'line_group': '',
		'line_count': 0
	}


def test_clear_progress(capsys : CaptureFixture[str]) -> None:
	clear_progress()

	assert capsys.readouterr().err == choices.progress_action_set.get('cursor_start') + choices.progress_action_set.get('erase_line')
