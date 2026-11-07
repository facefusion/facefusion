import shutil
import time
from contextlib import contextmanager
from functools import partial
from types import SimpleNamespace
from typing import Iterator

from facefusion import process_manager
from facefusion.clis import stream as cli_stream
from facefusion.clis.formatter import colorize, create_line, get_line_offset, resolve_line_group
from facefusion.types import Progress, StageType


@contextmanager
def create() -> Iterator[SimpleNamespace]:
	progress = SimpleNamespace(
		time_update = 0.0
	)
	progress.update = partial(update, progress)

	yield progress

	cli_stream.write('')


def update(progress : SimpleNamespace) -> None:
	stages = process_manager.get_stages()
	time_current = time.monotonic()

	if stages and time_current - progress.time_update > 0.5:
		progress.time_update = time_current
		render(stages[-1].get('progress'), stages[-1].get('title'), stages[-1].get('type'))


def render(progress : Progress, title : str, stage_type : StageType) -> None:
	description = progress.get('description')
	status = str(progress.get('current'))

	if progress.get('unit') == 'frame':
		status = resolve_frame(progress)

	if progress.get('unit') == 'download':
		status = resolve_download(progress)

	progress_width = shutil.get_terminal_size().columns - get_line_offset() - len(title) - len(status) - 2

	if description:
		progress_width -= len(description) + 3

	progress_width = min(progress_width, 50)

	progress_fill = 0

	if progress.get('total') > 0:
		progress_fill = progress.get('current') * progress_width // progress.get('total')

	progress_bar = colorize('=' * progress_fill, 'white') + colorize('=' * (progress_width - progress_fill), 'grey')
	progress_parts = [ title, progress_bar, status ]

	if description:
		progress_parts.append('|')
		progress_parts.append(description)

	line_group = resolve_line_group()
	cli_stream.write(create_line(line_group.get('label'), line_group.get('color'), '▶', stage_type, ' '.join(progress_parts)))


def resolve_rate(progress : Progress) -> float:
	progress_duration = progress.get('updated_at') - progress.get('started_at')

	if progress_duration > 0:
		return progress.get('current') / progress_duration

	return 0.0


def resolve_frame(progress : Progress) -> str:
	return str(round(resolve_rate(progress), 1)) + 'frame/s'


def resolve_download(progress : Progress) -> str:
	rate = resolve_rate(progress)

	if rate > 1024 * 1024:
		return str(round(rate / (1024 * 1024), 1)) + 'mb/s'

	return str(round(rate / 1024, 1)) + 'kb/s'
