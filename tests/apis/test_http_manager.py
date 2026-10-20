import asyncio
from typing import Iterator

import pytest

from facefusion import store_creator
from facefusion.apis.http_manager import HTTP_STORE, destroy, end_request, has_request, init, start_request
from facefusion.session_context import resolve_local_id, set_session_id


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = resolve_local_id()

	set_session_id(local_id)
	init()

	yield

	set_session_id(local_id)


def test_init() -> None:
	set_session_id('session-a')
	init()

	assert store_creator.get_content(HTTP_STORE, 'session-a') == {}

	destroy('session-a')


@pytest.mark.asyncio
async def test_has_request() -> None:
	assert has_request('upload') is False

	start_request('upload', asyncio.current_task())

	assert has_request('upload') is True
	assert has_request('invalid') is False

	set_session_id('session-a')

	assert has_request('upload') is False


@pytest.mark.asyncio
async def test_start_request() -> None:
	start_request('upload', asyncio.current_task())
	session_http = store_creator.get_content(HTTP_STORE, resolve_local_id()).get('upload')[0]

	assert session_http.get('task') == asyncio.current_task()
	assert session_http.get('event_loop') == asyncio.get_running_loop()

	set_session_id('session-a')
	start_request('upload', asyncio.current_task())

	assert store_creator.has_content(HTTP_STORE, 'session-a') is False


@pytest.mark.asyncio
async def test_end_request() -> None:
	http_task_1 = asyncio.create_task(asyncio.sleep(0))
	http_task_2 = asyncio.create_task(asyncio.sleep(0))
	start_request('upload', http_task_1)
	start_request('upload', http_task_2)
	end_request('upload', http_task_1)

	assert store_creator.get_content(HTTP_STORE, resolve_local_id()).get('upload')[0].get('task') == http_task_2

	end_request('upload', http_task_2)

	assert store_creator.get_content(HTTP_STORE, resolve_local_id()) == {}

	end_request('upload', http_task_1)

	assert store_creator.get_content(HTTP_STORE, resolve_local_id()) == {}

	set_session_id('session-a')
	end_request('upload', http_task_1)

	assert store_creator.has_content(HTTP_STORE, 'session-a') is False

	await asyncio.wait([ http_task_1, http_task_2 ])


@pytest.mark.asyncio
async def test_destroy() -> None:
	http_task = asyncio.create_task(asyncio.sleep(10))
	set_session_id('session-a')
	init()

	start_request('upload', http_task)
	destroy('session-a')

	with pytest.raises(asyncio.CancelledError):
		await http_task

	assert http_task.cancelled() is True
	assert store_creator.has_content(HTTP_STORE, 'session-a') is False
