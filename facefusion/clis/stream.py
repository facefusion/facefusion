import sys
from logging import ERROR, LogRecord, WARNING

from facefusion import choices, session_context, session_manager, state_manager
from facefusion.common_helper import get_last
from facefusion.types import StreamLine

STREAM_LINE : StreamLine =\
{
	'line_group': '',
	'line_count': 0
}


def create_line(line_group : str, line_connector : str, line_type : str, line_text : str) -> str:
	group_label = line_group

	if line_connector == '│':
		group_label = ''

	return resolve_group_color(line_group) + group_label.ljust(8) + line_connector + ' ' + choices.color_palette.get('grey') + line_type.ljust(14) + choices.color_palette.get('reset') + '  ' + line_text


def get_line_offset() -> int:
	return len(create_line('server', '│', '', '')) - len(choices.color_palette.get('grey') * 2 + choices.color_palette.get('reset'))


def resolve_group_color(line_group : str) -> str:
	group_parts = line_group.split('.')

	if len(group_parts) == 2:
		return choices.color_palette.get(choices.stream_group_colors[int(group_parts[1]) % len(choices.stream_group_colors)])

	return choices.color_palette.get('grey')


def resolve_line_group() -> str:
	session_id = session_context.get_session_id()
	owner_id = session_manager.resolve_owner_id()
	local_id = session_context.resolve_local_id()

	if owner_id in session_manager.API_SESSIONS:
		return 'api.' + str(list(session_manager.API_SESSIONS).index(owner_id))

	if session_id == local_id and state_manager.get_item('command') == 'api':
		return 'server'

	if session_id in session_manager.CLI_SESSIONS:
		return 'cli.' + str(list(session_manager.CLI_SESSIONS).index(session_id))

	return 'cli.0'


def create_group_line(line_group : str, line_type : str, line_text : str) -> str:
	line_connector = '┬'

	if line_group == STREAM_LINE.get('line_group') and STREAM_LINE.get('line_count') < 20:
		line_connector = '│'

	if line_connector == '┬':
		STREAM_LINE['line_count'] = 0

	STREAM_LINE['line_group'] = line_group
	STREAM_LINE['line_count'] += 1
	return create_line(line_group, line_connector, line_type, line_text)


def format_record(record : LogRecord) -> bool:
	module_name = record.__dict__.get('module_name')

	if record.name == 'facefusion' and module_name:
		record.msg = create_group_line(resolve_line_group(), get_last(module_name.split('.')), color_message(record.getMessage(), record.levelno))
		record.args = ()

	if record.name == 'facefusion' and not module_name:
		clear_line()

	return True


def color_message(message : str, log_level : int) -> str:
	if log_level == WARNING:
		return choices.color_palette.get('yellow') + message + choices.color_palette.get('reset')

	if log_level == ERROR:
		return choices.color_palette.get('red') + message + choices.color_palette.get('reset')

	return message


def write(text : str) -> None:
	sys.stderr.write(choices.progress_action_set.get('cursor_start') + choices.progress_action_set.get('erase_line') + text)
	sys.stderr.flush()


def flush() -> None:
	sys.stderr.flush()


def write_progress(text : str) -> None:
	sys.stderr.write(choices.progress_action_set.get('cursor_start') + text + choices.progress_action_set.get('erase_line'))
	sys.stderr.flush()


def clear_line() -> None:
	STREAM_LINE['line_group'] = ''
	STREAM_LINE['line_count'] = 0


def clear_progress() -> None:
	sys.stderr.write(choices.progress_action_set.get('cursor_start') + choices.progress_action_set.get('erase_line'))
	sys.stderr.flush()
