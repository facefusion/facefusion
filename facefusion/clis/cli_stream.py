import os
import sys
from functools import partial
from logging import LogRecord
from logging.handlers import BufferingHandler

from facefusion import choices
from facefusion.clis.cli_formatter import create_log_line, format_log_line
from facefusion.types import LogLine


def create_handler() -> BufferingHandler:
	buffering_handler = BufferingHandler(1)
	buffering_handler.emit = partial(emit, buffering_handler) #type:ignore[method-assign]
	return buffering_handler


def emit(buffering_handler : BufferingHandler, log_record : LogRecord) -> None:
	previous_line : LogLine = []

	for previous_record in buffering_handler.buffer:
		previous_line = create_log_line(previous_record)

	write(format_log_line(previous_line, create_log_line(log_record)) + os.linesep)
	buffering_handler.buffer = [ log_record ]


def write(message : str) -> None:
	sys.stderr.write(choices.progress_action_set.get('cursor_start') + choices.progress_action_set.get('erase_line') + message)
	sys.stderr.flush()
