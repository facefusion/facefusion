from typing import List, Tuple

from facefusion.logger import get_package_logger
from facefusion.types import TableContent, TableHeader


def render(headers : List[TableHeader], contents : List[List[TableContent]]) -> None:
	package_logger = get_package_logger()
	table_column, table_top, table_middle, table_bottom = create_table_parts(headers, contents)

	package_logger.critical(table_top)
	package_logger.critical(table_column.format(*headers))
	package_logger.critical(table_middle)

	for content in contents:
		content = [ str(value) for value in content ]
		package_logger.critical(table_column.format(*content))

	package_logger.critical(table_bottom)


def create_table_parts(headers : List[TableHeader], contents : List[List[TableContent]]) -> Tuple[str, str, str, str]:
	column_parts = []
	separator_parts = []
	widths = [ len(header) for header in headers ]

	for content in contents:
		for index, value in enumerate(content):
			widths[index] = max(widths[index], len(str(value)))

	for width in widths:
		column_parts.append('{:<' + str(width) + '}')
		separator_parts.append('─' * width)

	table_column = '│ ' + ' │ '.join(column_parts) + ' │'
	table_top = '┌─' + '─┬─'.join(separator_parts) + '─┐'
	table_middle = '├─' + '─┼─'.join(separator_parts) + '─┤'
	table_bottom = '└─' + '─┴─'.join(separator_parts) + '─┘'

	return table_column, table_top, table_middle, table_bottom
