import logging
from typing import Iterator

import pytest
from _pytest.logging import LogCaptureFixture

from facefusion.logger import create_message, debug, disable, enable, error, get_package_logger, info, init, warn


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
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

	assert caplog.record_tuples == [ ('facefusion', logging.DEBUG, '[FACEFUSION.CORE] message') ]


def test_info(caplog : LogCaptureFixture) -> None:
	info('message', 'facefusion.core')

	assert caplog.record_tuples == [ ('facefusion', logging.INFO, '[FACEFUSION.CORE] message') ]


def test_warn(caplog : LogCaptureFixture) -> None:
	warn('message', 'facefusion.core')

	assert caplog.record_tuples == [ ('facefusion', logging.WARNING, '[FACEFUSION.CORE] message') ]


def test_error(caplog : LogCaptureFixture) -> None:
	error('message', 'facefusion.core')

	assert caplog.record_tuples == [ ('facefusion', logging.ERROR, '[FACEFUSION.CORE] message') ]


def test_create_message() -> None:
	assert create_message('message', 'facefusion.processors.modules.face_swapper.core') == '[FACEFUSION.CORE] message'
	assert create_message('message', 'facefusion') == '[FACEFUSION.FACEFUSION] message'
	assert create_message('message', '') == 'message'


def test_enable(caplog : LogCaptureFixture) -> None:
	disable()
	enable()
	info('message', 'facefusion.core')

	assert get_package_logger().disabled is False
	assert caplog.messages == [ '[FACEFUSION.CORE] message' ]


def test_disable(caplog : LogCaptureFixture) -> None:
	disable()
	info('message', 'facefusion.core')

	assert get_package_logger().disabled is True
	assert caplog.messages == []
