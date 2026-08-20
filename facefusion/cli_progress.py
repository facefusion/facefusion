import os
import shutil
import sys
import time
from contextlib import contextmanager
from functools import partial
from types import SimpleNamespace
from typing import Iterator, Sized

from facefusion import choices
from facefusion.types import ProgressMode


@contextmanager
def create(mode : ProgressMode = 'frame', current : int = 0, total : int = 0, moment : float = 0.5) -> Iterator[SimpleNamespace]:
	progress = SimpleNamespace(
		mode = mode,
		current = current,
		total = total,
		moment = moment,
		time_start = time.monotonic()
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

	if time.monotonic() - progress.moment > 0.1:
		progress.moment = time.monotonic()
		render(progress)


def resolve_status(progress : SimpleNamespace) -> str:
	if progress.mode == 'percent' and progress.total > 0:
		percent = progress.current * 100 // progress.total
		return str(percent) + '%'

	if progress.mode == 'frame':
		rate = round(resolve_rate(progress), 1)
		return str(rate) + ' frames/s'

	if progress.mode == 'download':
		rate = resolve_rate(progress)

		if rate > 1024 * 1024:
			rate = round(rate / (1024 * 1024), 1)
			return str(rate) + ' mb/s'

		rate = round(rate / 1024, 1)
		return str(rate) + ' kb/s'

	return str(progress.current)


def resolve_rate(progress : SimpleNamespace) -> float:
	if time.monotonic() - progress.time_start > 0:
		return progress.current / (time.monotonic() - progress.time_start)

	return 0.0


def render(progress : SimpleNamespace) -> None:
	title = getattr(progress, 'title', '')
	description = getattr(progress, 'description', '')
	status = resolve_status(progress)

	progress_width = shutil.get_terminal_size().columns - len(title) - len(status) - len(description) - 3

	if progress.total > 0:
		progress_fill = progress.current * progress_width // progress.total
	else:
		progress_fill = 0

	sys.stdout.write(choices.terminal_action_set.get('cursor_start') + ' '.join(
	[
		title,
		choices.terminal_action_set.get('color_active') + '=' * progress_fill + choices.terminal_action_set.get('color_neutral') + '=' * (progress_width - progress_fill) + choices.terminal_action_set.get('reset'),
		status,
		description
	]) + choices.terminal_action_set.get('erase_line'))
	sys.stdout.flush()
