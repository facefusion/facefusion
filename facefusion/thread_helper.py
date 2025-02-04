<<<<<<< HEAD
from typing import List, Union, ContextManager
import threading
from contextlib import nullcontext
=======
import threading
from contextlib import nullcontext
from typing import ContextManager, Union

from facefusion.execution import has_execution_provider
>>>>>>> origin/master

THREAD_LOCK : threading.Lock = threading.Lock()
THREAD_SEMAPHORE : threading.Semaphore = threading.Semaphore()
NULL_CONTEXT : ContextManager[None] = nullcontext()


def thread_lock() -> threading.Lock:
	return THREAD_LOCK


def thread_semaphore() -> threading.Semaphore:
	return THREAD_SEMAPHORE


<<<<<<< HEAD
def conditional_thread_semaphore(execution_providers : List[str]) -> Union[threading.Semaphore, ContextManager[None]]:
	if 'DmlExecutionProvider' in execution_providers:
=======
def conditional_thread_semaphore() -> Union[threading.Semaphore, ContextManager[None]]:
	if has_execution_provider('directml') or has_execution_provider('rocm'):
>>>>>>> origin/master
		return THREAD_SEMAPHORE
	return NULL_CONTEXT
