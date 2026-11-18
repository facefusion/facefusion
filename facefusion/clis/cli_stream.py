import sys
import threading
from functools import partial
from logging import LogRecord, StreamHandler
from logging.handlers import MemoryHandler
from types import SimpleNamespace
from typing import Dict, List

from facefusion import choices
from facefusion.clis.cli_formatter import format_record


def create_handler() -> MemoryHandler:
	stream_handler = StreamHandler(SimpleNamespace(write = write, flush = sys.stderr.flush))
	stream_handler.format = partial(format_record, []) #type:ignore[method-assign]
	memory_handler = MemoryHandler(1024, target = stream_handler)
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
		record_set : Dict[str, List[LogRecord]] = {}

		for record in memory_handler.buffer:
			log_group = record.__dict__.get('log_group') or {}
			record_set.setdefault(log_group.get('group_label'), []).append(record)

		memory_handler.buffer = []

		for records in record_set.values():
			memory_handler.buffer.extend(records)

		MemoryHandler.flush(memory_handler)


def write(text : str) -> None:
	sys.stderr.write(choices.progress_action_set.get('cursor_start') + choices.progress_action_set.get('erase_line') + text)
	sys.stderr.flush()
