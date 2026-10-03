import asyncio
from typing import Iterator
from unittest.mock import AsyncMock

import pytest

from facefusion import store_creator
from facefusion.apis.websocket_store import WEBSOCKET_STORE, delete_websocket, destroy, init, set_websocket
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
async def test_set_websocket() -> None:
	websocket_mock = AsyncMock()

	set_websocket(websocket_mock)

	assert store_creator.get_content(WEBSOCKET_STORE, resolve_local_id()).get(id(websocket_mock)).get('websocket') is websocket_mock


@pytest.mark.asyncio
async def test_delete_websocket() -> None:
	websocket_mock = AsyncMock()

	set_websocket(websocket_mock)
	delete_websocket(websocket_mock)

	assert store_creator.get_content(WEBSOCKET_STORE, resolve_local_id()) == {}


@pytest.mark.asyncio
async def test_destroy() -> None:
	websocket_mock = AsyncMock()

	set_session_id('session-a')
	init()
	set_websocket(websocket_mock)
	await asyncio.to_thread(destroy, 'session-a')

	websocket_mock.close.assert_awaited_once()
	assert store_creator.has_content(WEBSOCKET_STORE, 'session-a') is False
