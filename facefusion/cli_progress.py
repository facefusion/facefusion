import os
import shutil
import sys
import threading
from datetime import datetime
from typing import List

from facefusion import choices, translator
from facefusion.types import RenderSet, Task

RENDER_SET : RenderSet =\
{
	'is_rendering': False,
	'slot_total': 0,
	'rendered_at': datetime.now(),
	'log_messages': []
}


def start_rendering() -> None:
	RENDER_SET['is_rendering'] = sys.stdout.isatty()
	RENDER_SET['rendered_at'] = datetime.now()

	if is_rendering():
		forward_native_logs()


def forward_native_logs() -> None:
	read_fd, write_fd = os.pipe()
	os.dup2(write_fd, sys.stderr.fileno())
	os.close(write_fd)
	threading.Thread(target = read_native_logs, args = (read_fd,), daemon = True).start()


def read_native_logs(read_fd : int) -> None:
	with os.fdopen(read_fd, errors = 'replace') as native_file:
		for log_line in native_file:
			if log_line.strip():
				queue_log(log_line.rstrip())


def is_rendering() -> bool:
	return RENDER_SET.get('is_rendering')


def queue_log(message : str) -> None:
	RENDER_SET.get('log_messages').append(message)


def write(text : str) -> None:
	if is_rendering():
		queue_log(text.rstrip(os.linesep))

	if not is_rendering():
		sys.stderr.write(text)


def flush() -> None:
	sys.stderr.flush()


def render_progresses(tasks : List[Task]) -> None:
	rendered_at = datetime.now()
	log_messages = RENDER_SET.get('log_messages')
	log_total = len(log_messages)
	running_tasks : List[Task] = []
	slot_lines : List[str] = []
	output_lines : List[str] = []
	output_parts : List[str] = []

	for log_message in log_messages[:log_total]:
		output_lines.extend(log_message.split(os.linesep))

	del log_messages[:log_total]

	for task in tasks:
		if not is_rendering() and task.get('state') == 'pending' and task.get('updated_at') > RENDER_SET.get('rendered_at'):
			output_lines.append(format_progress(task))

		if not task.get('state') == 'pending':
			running_tasks.append(task)

	if running_tasks:
		slot_lines.append(format_separator())

	for task in running_tasks:
		slot_lines.append(format_progress(task))

	if is_rendering():
		output_parts.append(choices.progress_action_set.get('cursor_up') * RENDER_SET.get('slot_total') + choices.progress_action_set.get('cursor_start'))
		RENDER_SET['slot_total'] = max(RENDER_SET.get('slot_total'), len(slot_lines))
		output_lines.extend([ '' ] * (RENDER_SET.get('slot_total') - len(slot_lines)))
		output_lines.extend(slot_lines)

	for output_line in output_lines:
		output_parts.append(output_line + resolve_line_end())

	RENDER_SET['rendered_at'] = rendered_at
	sys.stdout.write(''.join(output_parts))
	sys.stdout.flush()


def resolve_line_end() -> str:
	if is_rendering():
		return choices.progress_action_set.get('erase_line') + os.linesep

	return os.linesep


def format_separator() -> str:
	terminal_width = shutil.get_terminal_size().columns
	return choices.progress_action_set.get('color_neutral') + '\u2508' * terminal_width + choices.progress_action_set.get('reset')


def format_progress(task : Task) -> str:
	terminal_width = shutil.get_terminal_size().columns
	progress_width = 40
	progress_fill = resolve_fill(task, progress_width)
	progress_title = task.get('title')
	progress_color = choices.progress_action_set.get('color_active')

	if task.get('state') == 'stopping':
		progress_title = translator.get('stopping')
		progress_color = choices.progress_action_set.get('color_neutral')

	progress_bar = progress_color + '=' * progress_fill + choices.progress_action_set.get('color_neutral') + '=' * (progress_width - progress_fill) + choices.progress_action_set.get('reset')
	progress_meta : str = task.get('type')

	if task.get('description'):
		progress_meta += ' \u00b7 ' + task.get('description')

	progress_parts =\
	[
		progress_title.ljust(12),
		progress_bar,
		'  ' + resolve_count(task).ljust(12),
		resolve_rate_label(task).rjust(12),
		'  ' + choices.progress_action_set.get('color_neutral') + progress_meta[:max(terminal_width - 80, 0)] + choices.progress_action_set.get('reset')
	]
	return ''.join(progress_parts)


def resolve_fill(task : Task, progress_width : int) -> int:
	progress = task.get('progress')

	if progress.get('total'):
		return min(progress.get('current') * progress_width // progress.get('total'), progress_width)

	if 'total' in progress:
		return 0

	duration = (datetime.now() - task.get('created_at')).total_seconds()
	return int(duration % 2 / 2 * progress_width)


def resolve_count(task : Task) -> str:
	progress = task.get('progress')

	if 'total' in progress and progress.get('unit') == 'frame':
		return str(progress.get('current')) + ' / ' + str(progress.get('total'))

	if 'total' in progress:
		return resolve_percent(task)

	return str(progress.get('current'))


def resolve_rate_label(task : Task) -> str:
	unit = task.get('progress').get('unit')

	if unit == 'frame':
		return resolve_frame(task)

	if unit == 'download':
		return resolve_download(task)

	return ''


def resolve_rate(task : Task) -> float:
	duration = (task.get('updated_at') - task.get('created_at')).total_seconds()

	if duration > 0:
		return task.get('progress').get('current') / duration

	return 0.0


def resolve_percent(task : Task) -> str:
	progress = task.get('progress')

	if progress.get('total'):
		percent = progress.get('current') * 100 // progress.get('total')
		return str(percent) + ' %'

	return '0 %'


def resolve_frame(task : Task) -> str:
	rate = resolve_rate(task)
	return str(round(rate, 1)) + ' frame/s'


def resolve_download(task : Task) -> str:
	rate = resolve_rate(task)

	if rate > 1024 * 1024:
		return str(round(rate / (1024 * 1024), 1)) + ' mb/s'

	return str(round(rate / 1024, 1)) + ' kb/s'
