from logging import Logger, basicConfig, getLogger

import facefusion.choices
from facefusion.common_helper import get_first, get_last
from facefusion.types import LogLevel


def init(log_level : LogLevel) -> None:
	basicConfig(format = '%(message)s')
	get_package_logger().setLevel(facefusion.choices.log_level_set.get(log_level))


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
