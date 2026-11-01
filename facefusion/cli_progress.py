import os
import shutil
import sys
from datetime import datetime
from typing import List

from facefusion import choices
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
	output_parts : List[str] = []

	if is_rendering():
		output_parts.append(choices.progress_action_set.get('cursor_up') * RENDER_SET.get('slot_total') + choices.progress_action_set.get('cursor_start') + choices.progress_action_set.get('erase_down'))

	for log_message in log_messages[:log_total]:
		output_parts.append(log_message + os.linesep)

	del log_messages[:log_total]

	for task in tasks:
		if task.get('state') == 'pending' and task.get('updated_at') > RENDER_SET.get('rendered_at'):
			output_parts.append(format_progress(task) + os.linesep)

		if not task.get('state') == 'pending':
			running_tasks.append(task)

	if is_rendering():
		for task in running_tasks:
			output_parts.append(format_progress(task) + os.linesep)

		RENDER_SET['slot_total'] = len(running_tasks)

	RENDER_SET['rendered_at'] = rendered_at
	sys.stdout.write(''.join(output_parts))
	sys.stdout.flush()


def format_progress(task : Task) -> str:
	title = task.get('title')
	description = task.get('description')
	status = resolve_status(task)
	progress_width = shutil.get_terminal_size().columns - len(title) - len(status) - 2

	if description:
		progress_width -= len(description) + 3

	progress_fill = resolve_fill(task, progress_width)
	progress_bar = choices.progress_action_set.get('color_active') + '=' * progress_fill + choices.progress_action_set.get('color_neutral') + '=' * (progress_width - progress_fill) + choices.progress_action_set.get('reset')
	progress_parts = [ title, progress_bar, status ]

	if description:
		progress_parts.append('|')
		progress_parts.append(description)

	return ' '.join(progress_parts)


def resolve_fill(task : Task, progress_width : int) -> int:
	progress = task.get('progress')

	if progress.get('total'):
		return progress.get('current') * progress_width // progress.get('total')

	if 'total' in progress:
		return 0

	duration = (datetime.now() - task.get('created_at')).total_seconds()
	return int(duration % 2 / 2 * progress_width)


def resolve_status(task : Task) -> str:
	unit = task.get('progress').get('unit')

	if unit == 'frame':
		return resolve_frame(task)

	if unit == 'download':
		return resolve_download(task)

	return resolve_percent(task)


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
	return str(round(rate, 1)) + 'frame/s'


def resolve_download(task : Task) -> str:
	rate = resolve_rate(task)

	if rate > 1024 * 1024:
		return str(round(rate / (1024 * 1024), 1)) + 'mb/s'

	return str(round(rate / 1024, 1)) + 'kb/s'
