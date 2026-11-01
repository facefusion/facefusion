import os
from logging import Formatter, LogRecord, Logger, basicConfig, getLogger

import facefusion.choices
from facefusion import cli_progress
from facefusion.common_helper import get_first, get_last
from facefusion.types import LogLevel


def init(log_level : LogLevel) -> None:
	basicConfig(format = '%(message)s', stream = cli_progress)
	get_package_logger().setLevel(facefusion.choices.log_level_set.get(log_level))


def forward_server_logs() -> None:
	package_logger = get_package_logger()

	for server_logger in [ getLogger('uvicorn.error'), getLogger('uvicorn.access') ]:
		server_logger.handlers = []
		server_logger.propagate = False
		server_logger.setLevel(package_logger.level)
		server_logger.addFilter(capture_server_log)


def capture_server_log(log_record : LogRecord) -> bool:
	log_message = log_record.getMessage()

	if log_record.exc_info:
		log_message += os.linesep + Formatter().formatException(log_record.exc_info)

	if log_record.levelname == 'DEBUG':
		debug(log_message, 'facefusion.api')

	if log_record.levelname == 'INFO':
		info(log_message, 'facefusion.api')

	if log_record.levelname == 'WARNING':
		warn(log_message, 'facefusion.api')

	if log_record.levelname in [ 'ERROR', 'CRITICAL' ]:
		error(log_message, 'facefusion.api')

	return False


def get_package_logger() -> Logger:
	return getLogger('facefusion')


def debug(message : str, module_name : str) -> None:
	get_package_logger().debug(create_message(message, module_name))


def info(message : str, module_name : str) -> None:
	get_package_logger().info(create_message(message, module_name))


def warn(message : str, module_name : str) -> None:
	get_package_logger().warning(create_message(message, module_name))


def error(message : str, module_name : str) -> None:
	get_package_logger().error(create_message(message, module_name))


def create_message(message : str, module_name : str) -> str:
	module_names = module_name.split('.')
	first_module_name = get_first(module_names)
	last_module_name = get_last(module_names)

	if first_module_name and last_module_name:
		return '[' + first_module_name.upper() + '.' + last_module_name.upper() + '] ' + message
	return message


def enable() -> None:
	get_package_logger().disabled = False


def disable() -> None:
	get_package_logger().disabled = True
