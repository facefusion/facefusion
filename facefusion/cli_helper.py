from typing import Tuple

from facefusion.logger import get_package_logger
from facefusion.types import TableContents, TableHeaders


def render_table(headers : TableHeaders, contents : TableContents) -> None:
	package_logger = get_package_logger()
	table_column, table_separator = create_table_parts(headers, contents)

	package_logger.critical(table_separator)
	package_logger.critical(table_column.format(*headers))
	package_logger.critical(table_separator)

	for content in contents:
		content = [ str(value) for value in content ]
		package_logger.critical(table_column.format(*content))

	package_logger.critical(table_separator)


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
