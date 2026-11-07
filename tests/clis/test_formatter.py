import logging

import pytest

from facefusion import choices, session_context, session_manager, state_manager
from facefusion.clis.formatter import color_message, colorize, create_group_state, create_line, create_line_group, format_record, get_line_offset, register_line, resolve_line_group, sort_records


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()


def test_create_group_state() -> None:
	assert create_group_state() ==\
	{
		'label': '',
		'line_count': 0
	}


def test_format_record() -> None:
	group_state = create_group_state()
	core_record = logging.makeLogRecord({ 'name': 'facefusion', 'msg': 'processing step 1 of 1', 'module_name': 'facefusion.core', 'line_group': create_line_group('cli', 0) })
	warn_record = logging.makeLogRecord({ 'name': 'facefusion', 'msg': 'no face detected', 'levelno': logging.WARNING, 'module_name': 'facefusion.face_detector', 'line_group': create_line_group('cli', 0) })
	table_record = logging.makeLogRecord({ 'name': 'facefusion', 'msg': '+---+' })

	assert format_record(group_state, core_record) == create_line('cli.0', 'cyan', '┬', 'core', 'processing step 1 of 1')
	assert format_record(group_state, warn_record) == create_line('', 'cyan', '│', 'face_detector', color_message('no face detected', logging.WARNING))
	assert format_record(group_state, table_record) == '+---+'
	assert group_state == create_group_state()
	assert format_record(group_state, core_record) == create_line('cli.0', 'cyan', '┬', 'core', 'processing step 1 of 1')


def test_sort_records() -> None:
	first_record = logging.makeLogRecord({ 'msg': 'first', 'line_group': create_line_group('api', 0) })
	second_record = logging.makeLogRecord({ 'msg': 'second', 'line_group': create_line_group('api', 1) })
	third_record = logging.makeLogRecord({ 'msg': 'third', 'line_group': create_line_group('api', 0) })
	table_record = logging.makeLogRecord({ 'msg': '+---+' })

	assert sort_records([ first_record, second_record, third_record, table_record ]) == [ first_record, third_record, second_record, table_record ]


def test_register_line() -> None:
	group_state = create_group_state()

	assert register_line(group_state, create_line_group('api', 0)) is True
	assert register_line(group_state, create_line_group('api', 0)) is False
	assert register_line(group_state, create_line_group('api', 1)) is True

	for _ in range(18):
		register_line(group_state, create_line_group('api', 1))

	assert register_line(group_state, create_line_group('api', 1)) is False
	assert register_line(group_state, create_line_group('api', 1)) is True


def test_color_message() -> None:
	assert color_message('message', logging.INFO) == 'message'
	assert color_message('message', logging.WARNING) == colorize('message', 'yellow')
	assert color_message('message', logging.ERROR) == colorize('message', 'red')


def test_colorize() -> None:
	assert colorize('message', 'cyan') == choices.color_palette.get('cyan') + 'message' + choices.color_palette.get('reset')


def test_create_line() -> None:
	assert create_line('api.1', 'magenta', '┬', 'core', 'message') == colorize('api.1   ┬', 'magenta') + ' ' + colorize('core          ', 'grey') + '  message'
	assert create_line('', 'magenta', '│', 'inference_manager', 'message') == colorize('        │', 'magenta') + ' ' + colorize('inference_manager', 'grey') + '  message'


def test_get_line_offset() -> None:
	assert get_line_offset() == len(''.ljust(8) + '│' + ' ' + ''.ljust(14) + '  ')


def test_resolve_line_group() -> None:
	local_id = session_context.resolve_local_id()

	assert resolve_line_group() == create_line_group('cli', 0)

	session_manager.set_cli_session(local_id, session_manager.create_cli_session())
	session_manager.fork_session()

	assert resolve_line_group() == create_line_group('cli', 1)

	session_manager.join_session()
	session_manager.clear_cli_session(local_id)
	session_manager.set_api_session('api-session-1', session_manager.create_api_session())
	session_manager.set_api_session('api-session-2', session_manager.create_api_session())
	session_context.set_session_id('api-session-2')

	assert resolve_line_group() == create_line_group('api', 1)

	session_manager.fork_session()

	assert resolve_line_group() == create_line_group('api', 1)

	session_manager.join_session()
	session_context.set_session_id(local_id)
	session_manager.clear_api_session('api-session-1')
	session_manager.clear_api_session('api-session-2')
	state_manager.init_item('command', 'api')

	assert resolve_line_group() ==\
	{
		'label': 'server',
		'color': 'grey'
	}

	state_manager.clear_item('command')


def test_create_line_group() -> None:
	assert create_line_group('api', 0) ==\
	{
		'label': 'api.0',
		'color': 'cyan'
	}
	assert create_line_group('cli', 6).get('color') == 'magenta'
