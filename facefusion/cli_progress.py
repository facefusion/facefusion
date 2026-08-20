import os
import shutil
import sys
import time
from contextlib import contextmanager
from functools import partial
from types import SimpleNamespace
from typing import Iterator, Sized

from facefusion import choices
from facefusion.types import ProgressUnit


@contextmanager
def create(unit : ProgressUnit = 'frame', current : int = 0, total : int = 0) -> Iterator[SimpleNamespace]:
	progress = SimpleNamespace(
		unit = unit,
		current = current,
		total = total,
		time_start = time.monotonic(),
		time_update = 0.0
	)
	progress.count = partial(count, progress)
	progress.set_title = partial(set_title, progress)
	progress.set_description = partial(set_description, progress)
	progress.update = partial(update, progress)
	progress.seek = partial(seek, progress)

	yield progress

	progress.current = progress.total
	render(progress)

	sys.stdout.flush()
	sys.stdout.write(os.linesep)


def set_title(progress : SimpleNamespace, title : str) -> None:
	progress.title = title


def set_description(progress : SimpleNamespace, description : str) -> None:
	progress.description = description


def count(progress : SimpleNamespace, collection : Sized) -> None:
	progress.total = len(collection)


def update(progress : SimpleNamespace) -> None:
	seek(progress, progress.current + 1)


def seek(progress : SimpleNamespace, current : int) -> None:
	progress.current = current
	time_current = time.monotonic()

	if time_current - progress.time_update > 0.5:
		progress.time_update = time_current
		render(progress)


def render(progress : SimpleNamespace) -> None:
	title = getattr(progress, 'title', '')
	description = getattr(progress, 'description', '')
	status = str(progress.current)

	if progress.unit == 'percent':
		status = resolve_percent(progress)

	if progress.unit == 'frame':
		status = resolve_frame(progress)

	if progress.unit == 'download':
		status = resolve_download(progress)

	progress_width = shutil.get_terminal_size().columns - len(title) - len(status) - 2

	if description:
		progress_width -= len(description) + 3

	if progress.total > 0:
		progress_fill = progress.current * progress_width // progress.total
	else:
		progress_fill = 0

	progress_bar = choices.progress_action_set.get('color_active') + '=' * progress_fill + choices.progress_action_set.get('color_neutral') + '=' * (progress_width - progress_fill) + choices.progress_action_set.get('reset')
	progress_parts = [ title, progress_bar, status ]

	if description:
		progress_parts.append('|')
		progress_parts.append(description)

	sys.stdout.write(choices.progress_action_set.get('cursor_start') + ' '.join(progress_parts) + choices.progress_action_set.get('erase_line'))
	sys.stdout.flush()


def resolve_percent(progress : SimpleNamespace) -> str:
	if progress.total > 0:
		percent = progress.current * 100 // progress.total
		return str(percent) + ' %'

	return '0 %'


def resolve_frame(progress : SimpleNamespace) -> str:
	time_current = time.monotonic()

	if time_current - progress.time_start > 0:
		rate = progress.current / (time_current - progress.time_start)
		return str(round(rate, 1)) + 'frame/s'

	return '0.0frame/s'


def resolve_download(progress : SimpleNamespace) -> str:
	time_current = time.monotonic()

	if time_current - progress.time_start > 0:
		rate = progress.current / (time_current - progress.time_start)

		if rate > 1024 * 1024:
			return str(round(rate / (1024 * 1024), 1)) + 'mb/s'

		return str(round(rate / 1024, 1)) + 'kb/s'

	return '0.0kb/s'
