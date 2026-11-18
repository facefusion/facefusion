from logging import ERROR, LogRecord, WARNING

from facefusion import choices, session_context, session_manager, state_manager
from facefusion.common_helper import get_first, get_last
from facefusion.types import LogColor, LogGroup, LogLine


def create_log_line(log_record : LogRecord) -> LogLine:
	module_names = log_record.__dict__.get('module_names')
	log_group = log_record.__dict__.get('log_group')

	if module_names and log_group:
		return [ log_group.get('label'), get_last(module_names), color_message(log_record.getMessage(), log_record.levelno) ]

	return [ log_record.getMessage() ]


def format_log_line(previous_line : LogLine, current_line : LogLine) -> str:
	if len(current_line) == 3:
		line_label, line_type, line_text = current_line

		if line_label == get_first(previous_line):
			return create_line(str(), 'white', '│', line_type, line_text)

		return create_line(line_label, 'white', '┬', line_type, line_text)

	return get_first(current_line)


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
			'label': 'server',
			'color': 'grey'
		}

	if session_id in session_manager.CLI_SESSIONS:
		return create_log_group('cli', list(session_manager.CLI_SESSIONS).index(session_id))

	return create_log_group('cli', 0)


def create_log_group(group_name : str, group_index : int) -> LogGroup:
	return\
	{
		'label': group_name + '.' + str(group_index),
		'color': 'white'
	}
