import os
import sys
import threading
from functools import partial
from logging.handlers import MemoryHandler

from facefusion import choices
from facefusion.clis.cli_formatter import create_log_line, format_log_line
from facefusion.types import LogLine


def create_handler() -> MemoryHandler:
	memory_handler = MemoryHandler(1024)
	memory_handler.flush = partial(flush, memory_handler) #type:ignore[method-assign]
	start_timer(memory_handler)
	return memory_handler


def start_timer(memory_handler : MemoryHandler) -> None:
	flush_timer = threading.Timer(0.5, partial(end_timer, memory_handler))
	flush_timer.daemon = True
	flush_timer.start()


def end_timer(memory_handler : MemoryHandler) -> None:
	memory_handler.flush()
	start_timer(memory_handler)


def flush(memory_handler : MemoryHandler) -> None:
	with memory_handler.lock:
		previous_line : LogLine = []

		for log_record in memory_handler.buffer:
			current_line = create_log_line(log_record)
			write(format_log_line(previous_line, current_line) + os.linesep)
			previous_line = current_line

		memory_handler.buffer = []


def write(message : str) -> None:
	sys.stderr.write(choices.progress_action_set.get('cursor_start') + choices.progress_action_set.get('erase_line') + message)
	sys.stderr.flush()
