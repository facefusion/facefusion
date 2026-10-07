import asyncio
from typing import Iterator
from unittest.mock import AsyncMock

import pytest
from starlette.websockets import WebSocketState

from facefusion import store_creator
from facefusion.apis.websocket_store import WEBSOCKET_STORE, delete_websocket, destroy, has_websocket, init, set_websocket
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

	assert store_creator.get_content(WEBSOCKET_STORE, 'session-a') == {}

	destroy('session-a')


@pytest.mark.asyncio
async def test_has_websocket() -> None:
	websocket_mock = AsyncMock()

	assert has_websocket('stream') is False

	set_websocket('stream', websocket_mock)

	assert has_websocket('stream') is True
	assert has_websocket('metrics') is False


@pytest.mark.asyncio
async def test_set_websocket() -> None:
	websocket_mock = AsyncMock()

	set_websocket('stream', websocket_mock)

	assert store_creator.get_content(WEBSOCKET_STORE, resolve_local_id()).get('stream').get('websocket') is websocket_mock


@pytest.mark.asyncio
async def test_delete_websocket() -> None:
	websocket_mock = AsyncMock()

	set_websocket('stream', websocket_mock)
	delete_websocket('stream')

	assert store_creator.get_content(WEBSOCKET_STORE, resolve_local_id()) == {}


@pytest.mark.asyncio
async def test_destroy() -> None:
	websocket_mock_1 = AsyncMock(application_state = WebSocketState.CONNECTED)
	websocket_mock_2 = AsyncMock(application_state = WebSocketState.DISCONNECTED)

	set_session_id('session-a')
	init()

	set_websocket('metrics', websocket_mock_2)
	set_websocket('stream', websocket_mock_1)

	await asyncio.to_thread(destroy, 'session-a')

	assert websocket_mock_1.close.await_count == 1
	assert websocket_mock_2.close.await_count == 0

	assert store_creator.has_content(WEBSOCKET_STORE, 'session-a') is False
