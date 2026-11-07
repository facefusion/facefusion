import logging

from _pytest.capture import CaptureFixture

from facefusion import choices
from facefusion.clis.formatter import create_line_group
from facefusion.clis.stream import create_handler, write


def test_create_handler(capsys : CaptureFixture[str]) -> None:
	memory_handler = create_handler()

	for message, group_index in [ ('first', 0), ('second', 1), ('third', 0) ]:
		memory_handler.handle(logging.makeLogRecord({ 'msg': message, 'levelno': logging.INFO, 'module_name': 'facefusion.core', 'line_group': create_line_group('api', group_index) }))

	assert capsys.readouterr().err == ''

	memory_handler.flush()
	output = capsys.readouterr().err

	assert output.index('first') < output.index('third') < output.index('second')


def test_write(capsys : CaptureFixture[str]) -> None:
	write('hello\n')

	assert capsys.readouterr().err == choices.progress_action_set.get('cursor_start') + choices.progress_action_set.get('erase_line') + 'hello\n'
