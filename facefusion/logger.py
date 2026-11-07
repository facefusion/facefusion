from logging import Logger, StreamHandler, basicConfig, getLogger

import facefusion.choices
from facefusion.clis import stream as cli_stream
from facefusion.types import LogLevel


def init(log_level : LogLevel) -> None:
	stream_handler = StreamHandler(cli_stream)
	stream_handler.addFilter(cli_stream.format_record)
	basicConfig(format = '%(message)s', handlers = [ stream_handler ])
	get_package_logger().setLevel(facefusion.choices.log_level_set.get(log_level))


def get_package_logger() -> Logger:
	return getLogger('facefusion')


def debug(message : str, module_name : str) -> None:
	get_package_logger().debug(message, extra = { 'module_name': module_name })


def info(message : str, module_name : str) -> None:
	get_package_logger().info(message, extra = { 'module_name': module_name })


def warn(message : str, module_name : str) -> None:
	get_package_logger().warning(message, extra = { 'module_name': module_name })


def error(message : str, module_name : str) -> None:
	get_package_logger().error(message, extra = { 'module_name': module_name })


def enable() -> None:
	get_package_logger().disabled = False


def disable() -> None:
	get_package_logger().disabled = True
