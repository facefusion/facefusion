import signal
import sys
import tempfile
from typing import Iterator
from unittest.mock import patch

import pytest

from facefusion import process_manager, state_manager
from facefusion.exit_helper import fatal_exit, graceful_exit, hard_exit, signal_exit
from facefusion.filesystem import is_directory
from facefusion.temp_helper import create_temp_directory, get_temp_directory_path
from .assert_helper import get_test_output_path


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('output_path', get_test_output_path('target-240p.mp4'))


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	process_manager.start()
	create_temp_directory(state_manager.get_temp_path(), state_manager.get_item('output_path'))

	yield

	signal.signal(signal.SIGINT, signal.default_int_handler)
	process_manager.end()


def test_fatal_exit() -> None:
	with patch('os._exit') as os_mock:
		fatal_exit(1)

	assert os_mock.call_args.args == (1,)


def test_hard_exit() -> None:
	with pytest.raises(SystemExit) as system_exit:
		hard_exit(2)

	assert system_exit.value.code == 2


def test_signal_exit() -> None:
	with pytest.raises(SystemExit) as system_exit:
		signal_exit(signal.SIGINT, sys._getframe())

	assert system_exit.value.code == 0
	assert process_manager.is_stopping() is True
	assert is_directory(get_temp_directory_path(state_manager.get_temp_path(), state_manager.get_item('output_path'))) is False


def test_graceful_exit() -> None:
	with pytest.raises(SystemExit) as system_exit:
		graceful_exit(1)

	assert system_exit.value.code == 1
	assert signal.getsignal(signal.SIGINT) == signal.SIG_IGN
	assert process_manager.is_stopping() is True
	assert is_directory(get_temp_directory_path(state_manager.get_temp_path(), state_manager.get_item('output_path'))) is False
