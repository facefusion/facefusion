from logging import ERROR, LogRecord, WARNING
from typing import List

from facefusion import choices, session_context, session_manager, state_manager
from facefusion.common_helper import get_last
from facefusion.types import LogColor, LogGroup


def format_record(group_labels : List[str], record : LogRecord) -> str:
	module_name = record.__dict__.get('module_name')
	log_group = record.__dict__.get('log_group')

	if module_name and log_group:
		line_label = str()
		line_connector = '│'

		if not log_group.get('group_label') == get_last(group_labels) or len(group_labels) == 20:
			group_labels.clear()
			line_label = log_group.get('group_label')
			line_connector = '┬'

		group_labels.append(log_group.get('group_label'))
		return create_line(line_label, log_group.get('group_color'), line_connector, get_last(module_name.split('.')), color_message(record.getMessage(), record.levelno))

	group_labels.clear()
	return record.getMessage()


def color_message(message : str, log_level : int) -> str:
	if log_level == WARNING:
		return choices.log_character_set.get('yellow') + message + choices.log_character_set.get('reset')

	if log_level == ERROR:
		return choices.log_character_set.get('red') + message + choices.log_character_set.get('reset')

	return message


def create_line(line_label : str, line_color : LogColor, line_connector : str, line_type : str, line_text : str) -> str:
	return choices.log_character_set.get(line_color) + line_label.ljust(8) + line_connector + choices.log_character_set.get('reset') + ' ' + choices.log_character_set.get('grey') + line_type.ljust(14) + choices.log_character_set.get('reset') + '  ' + line_text


def resolve_log_group() -> LogGroup:
	session_id = session_context.get_session_id()
	owner_id = session_manager.resolve_owner_id()
	local_id = session_context.resolve_local_id()

	if owner_id in session_manager.API_SESSIONS:
		return create_log_group('api', list(session_manager.API_SESSIONS).index(owner_id))

	if session_id == local_id and state_manager.get_item('command') == 'api':
		return\
		{
			'group_label': 'server',
			'group_color': 'grey'
		}

	if session_id in session_manager.CLI_SESSIONS:
		return create_log_group('cli', list(session_manager.CLI_SESSIONS).index(session_id))

	return create_log_group('cli', 0)


def create_log_group(group_name : str, group_index : int) -> LogGroup:
	return\
	{
		'group_label': group_name + '.' + str(group_index),
		'group_color': 'white'
	}
