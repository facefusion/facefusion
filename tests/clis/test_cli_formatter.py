import logging
from typing import Iterator, List

import pytest

from facefusion import session_context, session_manager, state_manager
from facefusion.clis.cli_formatter import color_message, create_line, create_log_group, format_record, resolve_log_group


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	state_manager.init()

	yield

	session_manager.API_SESSIONS.clear()
	session_manager.CLI_SESSIONS.clear()
	state_manager.clear()


def test_format_record() -> None:
	group_labels : List[str] = []
	core_record = logging.makeLogRecord({ 'msg': 'message', 'levelno': logging.INFO, 'module_name': 'facefusion.core', 'log_group': create_log_group('cli', 0) })
	warn_record = logging.makeLogRecord({ 'msg': 'message', 'levelno': logging.WARNING, 'module_name': 'facefusion.face_detector', 'log_group': create_log_group('cli', 0) })
	table_record = logging.makeLogRecord({ 'msg': '+---+' })

	assert format_record(group_labels, core_record) == create_line('cli.0', 'white', '┬', 'core', 'message')
	assert format_record(group_labels, warn_record) == create_line('', 'white', '│', 'face_detector', color_message('message', logging.WARNING))
	assert format_record(group_labels, table_record) == '+---+'
	assert group_labels == []

	for _ in range(20):
		format_record(group_labels, core_record)

	assert format_record(group_labels, core_record) == create_line('cli.0', 'white', '┬', 'core', 'message')


def test_color_message() -> None:
	assert color_message('message', logging.INFO) == 'message'
	assert color_message('message', logging.WARNING) == '\033[38;5;221mmessage\033[0m'
	assert color_message('message', logging.ERROR) == '\033[38;5;204mmessage\033[0m'


def test_create_line() -> None:
	assert create_line('api.0', 'white', '┬', 'core', 'message') == '\033[38;5;250mapi.0   ┬\033[0m \033[38;5;244mcore          \033[0m  message'


def test_resolve_log_group() -> None:
	local_id = session_context.resolve_local_id()

	assert resolve_log_group() == create_log_group('cli', 0)

	session_manager.set_cli_session(local_id, session_manager.create_cli_session())
	session_manager.fork_session()

	assert resolve_log_group() == create_log_group('cli', 1)

	session_manager.join_session()
	session_manager.set_api_session('api-session-1', session_manager.create_api_session())
	session_manager.set_api_session('api-session-2', session_manager.create_api_session())
	session_context.set_session_id('api-session-2')

	assert resolve_log_group() == create_log_group('api', 1)

	session_context.set_session_id(local_id)
	state_manager.init_item('command', 'api')

	assert resolve_log_group() ==\
	{
		'group_label': 'server',
		'group_color': 'grey'
	}


def test_create_log_group() -> None:
	assert create_log_group('api', 0) ==\
	{
		'group_label': 'api.0',
		'group_color': 'white'
	}
	assert create_log_group('cli', 6) ==\
	{
		'group_label': 'cli.6',
		'group_color': 'white'
	}
