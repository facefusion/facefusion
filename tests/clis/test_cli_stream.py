import logging
import os
from unittest.mock import patch

from _pytest.capture import CaptureFixture

from facefusion import choices
from facefusion.clis.cli_formatter import create_line, create_log_group
from facefusion.clis.cli_stream import create_handler, write


def test_create_handler() -> None:
	with patch('threading.Timer') as threading_mock:
		memory_handler = create_handler()

	assert memory_handler.capacity == 1024
	assert threading_mock.call_args.args[0] == 0.5
	assert threading_mock.return_value.start.call_count == 1


def test_flush(capsys : CaptureFixture[str]) -> None:
	with patch('threading.Timer'):
		memory_handler = create_handler()

	for message, group_index in [ ('first', 0), ('second', 0), ('third', 1) ]:
		memory_handler.handle(logging.makeLogRecord({ 'msg': message, 'levelno': logging.INFO, 'module_names': [ 'facefusion', 'core' ], 'log_group': create_log_group('api', group_index) }))

	assert capsys.readouterr().err == str()

	memory_handler.flush()

	assert capsys.readouterr().err == choices.progress_action_set.get('cursor_start') + choices.progress_action_set.get('erase_line') + create_line('api.0', 'white', '┬', 'core', 'first') + os.linesep + choices.progress_action_set.get('cursor_start') + choices.progress_action_set.get('erase_line') + create_line(str(), 'white', '│', 'core', 'second') + os.linesep + choices.progress_action_set.get('cursor_start') + choices.progress_action_set.get('erase_line') + create_line('api.1', 'white', '┬', 'core', 'third') + os.linesep


def test_write(capsys : CaptureFixture[str]) -> None:
	write('message')

	assert capsys.readouterr().err == choices.progress_action_set.get('cursor_start') + choices.progress_action_set.get('erase_line') + 'message'
