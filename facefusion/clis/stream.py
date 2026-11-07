import sys
import threading
from functools import partial
from logging import StreamHandler
from logging.handlers import MemoryHandler
from types import SimpleNamespace

from facefusion import choices
from facefusion.clis.formatter import create_group_state, format_record, sort_records


def create_handler() -> MemoryHandler:
	stream_handler = StreamHandler(SimpleNamespace(write = write, flush = flush))
	stream_handler.format = partial(format_record, create_group_state()) #type:ignore[method-assign]
	memory_handler = MemoryHandler(1024, target = stream_handler)
	memory_handler.flush = partial(flush_records, memory_handler) #type:ignore[method-assign]
	start_flush_timer(memory_handler)
	return memory_handler


def flush_records(memory_handler : MemoryHandler) -> None:
	with memory_handler.lock:
		memory_handler.buffer = sort_records(memory_handler.buffer)
		MemoryHandler.flush(memory_handler)


def start_flush_timer(memory_handler : MemoryHandler) -> None:
	flush_timer = threading.Timer(choices.stream_flush_interval, partial(run_flush_timer, memory_handler))
	flush_timer.daemon = True
	flush_timer.start()


def run_flush_timer(memory_handler : MemoryHandler) -> None:
	memory_handler.flush()
	start_flush_timer(memory_handler)


def write(text : str) -> None:
	sys.stderr.write(choices.progress_action_set.get('cursor_start') + choices.progress_action_set.get('erase_line') + text)
	sys.stderr.flush()


def flush() -> None:
	sys.stderr.flush()
