from typing import Dict
from logging import basicConfig, getLogger, Logger, DEBUG, INFO, WARNING, ERROR

from facefusion.typing import LogLevel


def init(log_level : LogLevel) -> None:
	basicConfig(format = None)
	get_package_logger().setLevel(get_log_levels()[log_level])


def get_package_logger() -> Logger:
	return getLogger('facefusion')


def debug(message : str, scope : str) -> None:
	get_package_logger().debug('[' + scope + '] ' + message)


def info(message : str, scope : str) -> None:
	get_package_logger().info('[' + scope + '] ' + message)


def warn(message : str, scope : str) -> None:
	get_package_logger().warning('[' + scope + '] ' + message)


def error(message : str, scope : str) -> None:
	get_package_logger().error('[' + scope + '] ' + message)


def enable() -> None:
	get_package_logger().disabled = False


def disable() -> None:
	get_package_logger().disabled = True


def get_log_levels() -> Dict[LogLevel, int]:
	return\
	{
		'error': ERROR,
		'warn': WARNING,
		'info': INFO,
		'debug': DEBUG
	}
