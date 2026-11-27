import logging
import os

from _pytest.capture import CaptureFixture

from facefusion import choices
from facefusion.clis.cli_formatter import create_line, create_log_group
from facefusion.clis.cli_stream import create_handler, write


def test_create_handler() -> None:
	assert create_handler().capacity == 1


def test_emit(capsys : CaptureFixture[str]) -> None:
	buffering_handler = create_handler()

	for message, group_index in [ ('first', 0), ('second', 0), ('third', 1) ]:
		buffering_handler.handle(logging.makeLogRecord({ 'msg': message, 'levelno': logging.INFO, 'module_names': [ 'facefusion', 'core' ], 'log_group': create_log_group('api', group_index) }))

	assert capsys.readouterr().err == choices.progress_action_set.get('cursor_start') + choices.progress_action_set.get('erase_line') + create_line('api.0', 'white', '┬', 'core', 'first') + os.linesep + choices.progress_action_set.get('cursor_start') + choices.progress_action_set.get('erase_line') + create_line(str(), 'white', '│', 'core', 'second') + os.linesep + choices.progress_action_set.get('cursor_start') + choices.progress_action_set.get('erase_line') + create_line('api.1', 'white', '┬', 'core', 'third') + os.linesep
	assert len(buffering_handler.buffer) == 1


def test_write(capsys : CaptureFixture[str]) -> None:
	write('message')

	assert capsys.readouterr().err == choices.progress_action_set.get('cursor_start') + choices.progress_action_set.get('erase_line') + 'message'
