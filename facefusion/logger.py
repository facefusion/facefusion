from logging import Logger, basicConfig, getLogger
from typing import Tuple

from facefusion.choices import log_level_set
from facefusion.typing import LogLevel, TableContents, TableHeaders


def init(log_level : LogLevel) -> None:
	basicConfig(format = '%(message)s')
	get_package_logger().setLevel(log_level_set.get(log_level))


def get_package_logger() -> Logger:
	return getLogger('facefusion')


def debug(message : str, scope : str) -> None:
	get_package_logger().debug('[' + scope.upper() + '] ' + message)


def info(message : str, scope : str) -> None:
	get_package_logger().info('[' + scope.upper() + '] ' + message)


def warn(message : str, scope : str) -> None:
	get_package_logger().warning('[' + scope.upper() + '] ' + message)


def error(message : str, scope : str) -> None:
	get_package_logger().error('[' + scope.upper() + '] ' + message)


def table(headers : TableHeaders, contents : TableContents) -> None:
	package_logger = get_package_logger()
	table_column, table_separator = create_table_parts(headers, contents)

	package_logger.info(table_separator)
	package_logger.info(table_column.format(*headers))
	package_logger.info(table_separator)

	for content in contents:
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
