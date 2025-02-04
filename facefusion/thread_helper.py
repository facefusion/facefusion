from typing import List, Union, ContextManager
import threading
from contextlib import nullcontext

THREAD_LOCK : threading.Lock = threading.Lock()
THREAD_SEMAPHORE : threading.Semaphore = threading.Semaphore()
NULL_CONTEXT : ContextManager[None] = nullcontext()


def thread_lock() -> threading.Lock:
	return THREAD_LOCK


def thread_semaphore() -> threading.Semaphore:
	return THREAD_SEMAPHORE


def conditional_thread_semaphore(execution_providers : List[str]) -> Union[threading.Semaphore, ContextManager[None]]:
	if 'DmlExecutionProvider' in execution_providers:
		return THREAD_SEMAPHORE
	return NULL_CONTEXT
