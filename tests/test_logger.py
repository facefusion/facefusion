import logging
from typing import Iterator

import pytest
from _pytest.logging import LogCaptureFixture

from facefusion import state_manager
from facefusion.clis.cli_formatter import create_log_group
from facefusion.logger import create_extra, debug, disable, enable, error, get_package_logger, info, init, warn


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	state_manager.init()
	init('debug')

	yield

	get_package_logger().setLevel(logging.NOTSET)
	enable()


def test_init() -> None:
	init('error')

	assert get_package_logger().level == logging.ERROR

	init('debug')

	assert get_package_logger().level == logging.DEBUG


def test_get_package_logger() -> None:
	assert get_package_logger().name == 'facefusion'


def test_debug(caplog : LogCaptureFixture) -> None:
	debug('message', 'facefusion.core')

	assert caplog.record_tuples == [ ('facefusion', logging.DEBUG, 'message') ]
	assert caplog.records[0].__dict__.get('module_names') == [ 'facefusion', 'core' ]


def test_info(caplog : LogCaptureFixture) -> None:
	info('message', 'facefusion.core')

	assert caplog.record_tuples == [ ('facefusion', logging.INFO, 'message') ]
	assert caplog.records[0].__dict__.get('module_names') == [ 'facefusion', 'core' ]


def test_warn(caplog : LogCaptureFixture) -> None:
	warn('message', 'facefusion.core')

	assert caplog.record_tuples == [ ('facefusion', logging.WARNING, 'message') ]
	assert caplog.records[0].__dict__.get('module_names') == [ 'facefusion', 'core' ]


def test_error(caplog : LogCaptureFixture) -> None:
	error('message', 'facefusion.core')

	assert caplog.record_tuples == [ ('facefusion', logging.ERROR, 'message') ]
	assert caplog.records[0].__dict__.get('module_names') == [ 'facefusion', 'core' ]


def test_create_extra() -> None:
	assert create_extra('facefusion.core') ==\
	{
		'module_names': [ 'facefusion', 'core' ],
		'log_group': create_log_group('cli', 0)
	}


def test_enable_and_disable(caplog : LogCaptureFixture) -> None:
	disable()
	info('message', 'facefusion.core')

	assert get_package_logger().disabled is True
	assert caplog.messages == []

	enable()
	info('message', 'facefusion.core')

	assert get_package_logger().disabled is False
	assert caplog.messages == [ 'message' ]
