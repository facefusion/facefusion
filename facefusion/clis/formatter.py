from functools import partial
from logging import ERROR, LogRecord, WARNING
from typing import List

from facefusion import choices, session_context, session_manager, state_manager
from facefusion.common_helper import get_last
from facefusion.types import ColorName, GroupState, LineGroup


def create_group_state() -> GroupState:
	return\
	{
		'label': '',
		'line_count': 0
	}


def format_record(group_state : GroupState, record : LogRecord) -> str:
	module_name = record.__dict__.get('module_name')
	line_group = record.__dict__.get('line_group')

	if module_name and line_group:
		line_label = ''
		line_connector = '│'

		if register_line(group_state, line_group):
			line_label = line_group.get('label')
			line_connector = '┬'

		return create_line(line_label, line_group.get('color'), line_connector, get_last(module_name.split('.')), color_message(record.getMessage(), record.levelno))

	group_state.update(create_group_state())
	return record.getMessage()


def sort_records(records : List[LogRecord]) -> List[LogRecord]:
	record_labels = []

	for record in records:
		record_label = resolve_record_label(record)

		if record_label not in record_labels:
			record_labels.append(record_label)

	return sorted(records, key = partial(resolve_record_position, record_labels))


def resolve_record_label(record : LogRecord) -> str:
	line_group = record.__dict__.get('line_group')

	if line_group:
		return line_group.get('label')

	return str(id(record))


def resolve_record_position(record_labels : List[str], record : LogRecord) -> int:
	return record_labels.index(resolve_record_label(record))


def register_line(group_state : GroupState, line_group : LineGroup) -> bool:
	group_start = not line_group.get('label') == group_state.get('label') or group_state.get('line_count') == choices.stream_group_size

	if group_start:
		group_state['line_count'] = 0

	group_state['label'] = line_group.get('label')
	group_state['line_count'] += 1
	return group_start


def color_message(message : str, log_level : int) -> str:
	if log_level == WARNING:
		return colorize(message, 'yellow')

	if log_level == ERROR:
		return colorize(message, 'red')

	return message


def colorize(message : str, color_name : ColorName) -> str:
	return choices.color_palette.get(color_name) + message + choices.color_palette.get('reset')


def create_line(line_label : str, line_color : ColorName, line_connector : str, line_type : str, line_text : str) -> str:
	return colorize(line_label.ljust(8) + line_connector, line_color) + ' ' + colorize(line_type.ljust(14), 'grey') + '  ' + line_text


def get_line_offset() -> int:
	return 8 + 2 + 14 + 2


def resolve_line_group() -> LineGroup:
	session_id = session_context.get_session_id()
	owner_id = session_manager.resolve_owner_id()
	local_id = session_context.resolve_local_id()

	if owner_id in session_manager.API_SESSIONS:
		return create_line_group('api', list(session_manager.API_SESSIONS).index(owner_id))

	if session_id == local_id and state_manager.get_item('command') == 'api':
		return\
		{
			'label': 'server',
			'color': 'grey'
		}

	if session_id in session_manager.CLI_SESSIONS:
		return create_line_group('cli', list(session_manager.CLI_SESSIONS).index(session_id))

	return create_line_group('cli', 0)


def create_line_group(group_name : str, group_index : int) -> LineGroup:
	return\
	{
		'label': group_name + '.' + str(group_index),
		'color': choices.stream_group_colors[group_index % len(choices.stream_group_colors)]
	}

