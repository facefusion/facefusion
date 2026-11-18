import logging
from unittest.mock import patch

from _pytest.capture import CaptureFixture

from facefusion.clis.cli_formatter import create_line, create_log_group
from facefusion.clis.cli_stream import create_handler, write


def test_create_handler() -> None:
	with patch('threading.Timer') as threading_mock:
		memory_handler = create_handler()

	assert memory_handler.capacity == 1024
	assert threading_mock.call_args.args[0] == 0.5
	assert threading_mock.return_value.start.call_count == 1


def test_flush_records(capsys : CaptureFixture[str]) -> None:
	with patch('threading.Timer'):
		memory_handler = create_handler()

	for message, group_index in [ ('first', 0), ('second', 1), ('third', 0) ]:
		memory_handler.handle(logging.makeLogRecord({ 'msg': message, 'levelno': logging.INFO, 'module_name': 'facefusion.core', 'log_group': create_log_group('api', group_index) }))

	assert capsys.readouterr().err == ''

	memory_handler.flush()

	assert capsys.readouterr().err == '\033[G\033[K' + create_line('api.0', 'white', '┬', 'core', 'first') + '\n\033[G\033[K' + create_line('', 'white', '│', 'core', 'third') + '\n\033[G\033[K' + create_line('api.1', 'white', '┬', 'core', 'second') + '\n'


def test_write(capsys : CaptureFixture[str]) -> None:
	write('message')

	assert capsys.readouterr().err == '\033[G\033[Kmessage'
