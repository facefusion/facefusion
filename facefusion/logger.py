<<<<<<< HEAD
from typing import Dict
from logging import basicConfig, getLogger, Logger, DEBUG, INFO, WARNING, ERROR

from facefusion.typing import LogLevel


def init(log_level : LogLevel) -> None:
	basicConfig(format = None)
	get_package_logger().setLevel(get_log_levels()[log_level])
=======
from logging import Logger, basicConfig, getLogger
from typing import Tuple

import facefusion.choices
from facefusion.common_helper import get_first, get_last
from facefusion.typing import LogLevel, TableContents, TableHeaders


def init(log_level : LogLevel) -> None:
	basicConfig(format = '%(message)s')
	get_package_logger().setLevel(facefusion.choices.log_level_set.get(log_level))
>>>>>>> origin/master


def get_package_logger() -> Logger:
	return getLogger('facefusion')


<<<<<<< HEAD
def debug(message : str, scope : str) -> None:
	get_package_logger().debug('[' + scope + '] ' + message)


def info(message : str, scope : str) -> None:
	get_package_logger().info('[' + scope + '] ' + message)


def warn(message : str, scope : str) -> None:
	get_package_logger().warning('[' + scope + '] ' + message)


def error(message : str, scope : str) -> None:
	get_package_logger().error('[' + scope + '] ' + message)
=======
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
>>>>>>> origin/master


def enable() -> None:
	get_package_logger().disabled = False


def disable() -> None:
	get_package_logger().disabled = True
<<<<<<< HEAD


def get_log_levels() -> Dict[LogLevel, int]:
	return\
	{
		'error': ERROR,
		'warn': WARNING,
		'info': INFO,
		'debug': DEBUG
	}
=======
>>>>>>> origin/master
