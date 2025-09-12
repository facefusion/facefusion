import threading
from contextlib import nullcontext
from typing import ContextManager, Union

from facefusion.common_helper import is_linux, is_windows
from facefusion.execution import has_execution_provider

THREAD_LOCK : threading.Lock = threading.Lock()
THREAD_SEMAPHORE : threading.Semaphore = threading.Semaphore()
NULL_CONTEXT : ContextManager[None] = nullcontext()


def thread_lock() -> threading.Lock:
	return THREAD_LOCK


def thread_semaphore() -> threading.Semaphore:
	return THREAD_SEMAPHORE


def conditional_thread_semaphore() -> Union[threading.Semaphore, ContextManager[None]]:
	if is_windows() and has_execution_provider('directml') or is_linux() and has_execution_provider('migraphx') or is_linux() and has_execution_provider('rocm'):
		return THREAD_SEMAPHORE
	return NULL_CONTEXT
