import os
import shutil
import sys
import time
from contextlib import contextmanager
from functools import partial
from types import SimpleNamespace
from typing import Iterator

from facefusion import choices, process_manager
from facefusion.types import Progress


@contextmanager
def create() -> Iterator[SimpleNamespace]:
	progress = SimpleNamespace(
		time_update = 0.0
	)
	progress.update = partial(update, progress)

	yield progress

	stages = process_manager.get_stages()

	if stages:
		render(stages[-1].get('progress'), stages[-1].get('title'))

	sys.stdout.flush()
	sys.stdout.write(os.linesep)


def update(progress : SimpleNamespace) -> None:
	stages = process_manager.get_stages()
	time_current = time.monotonic()

	if stages and time_current - progress.time_update > 0.5:
		progress.time_update = time_current
		render(stages[-1].get('progress'), stages[-1].get('title'))


def render(progress : Progress, title : str) -> None:
	description = progress.get('description')
	status = str(progress.get('current'))

	if progress.get('unit') == 'percent':
		status = resolve_percent(progress)

	if progress.get('unit') == 'frame':
		status = resolve_frame(progress)

	if progress.get('unit') == 'download':
		status = resolve_download(progress)

	progress_width = shutil.get_terminal_size().columns - len(title) - len(status) - 2

	if description:
		progress_width -= len(description) + 3

	if progress.get('total') > 0:
		progress_fill = progress.get('current') * progress_width // progress.get('total')
	else:
		progress_fill = 0

	progress_bar = choices.progress_action_set.get('color_active') + '=' * progress_fill + choices.progress_action_set.get('color_neutral') + '=' * (progress_width - progress_fill) + choices.progress_action_set.get('reset')
	progress_parts = [ title, progress_bar, status ]

	if description:
		progress_parts.append('|')
		progress_parts.append(description)

	sys.stdout.write(choices.progress_action_set.get('cursor_start') + ' '.join(progress_parts) + choices.progress_action_set.get('erase_line'))
	sys.stdout.flush()


def resolve_percent(progress : Progress) -> str:
	if progress.get('total') > 0:
		percent = progress.get('current') * 100 // progress.get('total')
		return str(percent) + ' %'

	return '0 %'


def resolve_frame(progress : Progress) -> str:
	time_current = time.monotonic()

	if time_current - progress.get('started_at') > 0:
		rate = progress.get('current') / (time_current - progress.get('started_at'))
		return str(round(rate, 1)) + 'frame/s'

	return '0.0frame/s'


def resolve_download(progress : Progress) -> str:
	time_current = time.monotonic()

	if time_current - progress.get('started_at') > 0:
		rate = progress.get('current') / (time_current - progress.get('started_at'))

		if rate > 1024 * 1024:
			return str(round(rate / (1024 * 1024), 1)) + 'mb/s'

		return str(round(rate / 1024, 1)) + 'kb/s'

	return '0.0kb/s'
