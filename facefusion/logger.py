from logging import Logger, basicConfig, getLogger
from typing import Tuple

from facefusion.choices import log_level_set
from facefusion.common_helper import get_first, get_last
from facefusion.typing import LogLevel, TableContents, TableHeaders


def init(log_level : LogLevel) -> None:
	basicConfig(format = '%(message)s')
	get_package_logger().setLevel(log_level_set.get(log_level))


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
	scopes = module_name.split('.')
	first_scope = get_first(scopes)
	last_scope = get_last(scopes)

	if first_scope and last_scope:
		return '[' + first_scope.upper() + '.' + last_scope.upper() + '] ' + message
	return message


def table(headers : TableHeaders, contents : TableContents) -> None:
	package_logger = get_package_logger()
	table_column, table_separator = create_table_parts(headers, contents)

	package_logger.info(table_separator)
	package_logger.info(table_column.format(*headers))
	package_logger.info(table_separator)

	for content in contents:
		content = [ value if value else '' for value in content ]
		package_logger.info(table_column.format(*content))

	package_logger.info(table_separator)


def create_table_parts(headers : TableHeaders, contents : TableContents) -> Tuple[str, str]:
	column_parts = []
	separator_parts = []
	widths = [ len(header) for header in headers ]

	for content in contents:
		for index, value in enumerate(content):
			widths[index] = max(widths[index], len(str(value)))

	for width in widths:
		column_parts.append('{:<' + str(width) + '}')
		separator_parts.append('-' * width)

	return '| ' + ' | '.join(column_parts) + ' |', '+-' + '-+-'.join(separator_parts) + '-+'


def enable() -> None:
	get_package_logger().disabled = False


def disable() -> None:
	get_package_logger().disabled = True
