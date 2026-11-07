from logging import Logger, basicConfig, getLogger

import facefusion.choices
from facefusion.clis import stream as cli_stream
from facefusion.clis.formatter import resolve_line_group
from facefusion.types import LogExtra, LogLevel


def init(log_level : LogLevel) -> None:
	if not getLogger().handlers:
		basicConfig(format = '%(message)s', handlers = [ cli_stream.create_handler() ])

	get_package_logger().setLevel(facefusion.choices.log_level_set.get(log_level))


def get_package_logger() -> Logger:
	return getLogger('facefusion')


def debug(message : str, module_name : str) -> None:
	get_package_logger().debug(message, extra = create_extra(module_name))


def info(message : str, module_name : str) -> None:
	get_package_logger().info(message, extra = create_extra(module_name))


def warn(message : str, module_name : str) -> None:
	get_package_logger().warning(message, extra = create_extra(module_name))


def error(message : str, module_name : str) -> None:
	get_package_logger().error(message, extra = create_extra(module_name))


def create_extra(module_name : str) -> LogExtra:
	return\
	{
		'module_name': module_name,
		'line_group': resolve_line_group()
	}


def enable() -> None:
	get_package_logger().disabled = False


def disable() -> None:
	get_package_logger().disabled = True
