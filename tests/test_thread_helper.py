from typing import Iterator
from unittest.mock import patch

import pytest

from facefusion.session_context import get_session_id, resolve_local_id, set_session_id
from facefusion.thread_helper import NULL_CONTEXT, THREAD_LOCK, THREAD_SEMAPHORE, conditional_thread_semaphore, create_executor, thread_lock, thread_semaphore


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = resolve_local_id()

	set_session_id('session-a')

	yield

	set_session_id(local_id)


def test_thread_lock() -> None:
	assert thread_lock() is THREAD_LOCK


def test_thread_semaphore() -> None:
	assert thread_semaphore() is THREAD_SEMAPHORE


def test_conditional_thread_semaphore() -> None:
	with patch('platform.system', return_value = 'Linux'):
		with patch('onnxruntime.get_available_providers', return_value = [ 'CPUExecutionProvider' ]):
			assert conditional_thread_semaphore() is NULL_CONTEXT

		with patch('onnxruntime.get_available_providers', return_value = [ 'MIGraphXExecutionProvider' ]):
			assert conditional_thread_semaphore() is THREAD_SEMAPHORE

		with patch('onnxruntime.get_available_providers', return_value = [ 'DmlExecutionProvider' ]):
			assert conditional_thread_semaphore() is NULL_CONTEXT

	with patch('platform.system', return_value = 'Windows'):
		with patch('onnxruntime.get_available_providers', return_value = [ 'DmlExecutionProvider' ]):
			assert conditional_thread_semaphore() is THREAD_SEMAPHORE

		with patch('onnxruntime.get_available_providers', return_value = [ 'MIGraphXExecutionProvider' ]):
			assert conditional_thread_semaphore() is NULL_CONTEXT

	with patch('platform.system', return_value = 'Darwin'):
		with patch('onnxruntime.get_available_providers', return_value = [ 'CoreMLExecutionProvider' ]):
			assert conditional_thread_semaphore() is NULL_CONTEXT


def test_create_executor() -> None:
	with create_executor(1) as executor:
		assert executor.submit(get_session_id).result() == 'session-a'

	with create_executor(2) as executor:
		assert executor._max_workers == 2

	set_session_id('session-b')

	with create_executor(1) as executor:
		assert executor.submit(get_session_id).result() == 'session-b'

	with create_executor(1) as executor:
		set_session_id('session-a')

		assert executor.submit(get_session_id).result() == 'session-b'
