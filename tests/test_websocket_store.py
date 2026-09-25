from typing import Iterator
from unittest.mock import AsyncMock

import anyio
import pytest

from facefusion import store_creator
from facefusion.apis.websocket_store import WEBSOCKET_STORE, delete_websocket, destroy, init, set_websocket
from facefusion.session_context import resolve_local_id, set_session_id
from facefusion.types import SessionId, Websocket


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = resolve_local_id()

	set_session_id(local_id)
	init()

	yield

	set_session_id(local_id)


async def set_and_destroy_websocket(websocket : Websocket, session_id : SessionId) -> None:
	set_websocket(websocket)
	await anyio.to_thread.run_sync(destroy, session_id)


async def set_and_delete_websocket(websocket : Websocket) -> None:
	set_websocket(websocket)
	delete_websocket(websocket)


async def set_websocket_in_event_loop(websocket : Websocket) -> None:
	set_websocket(websocket)


def test_init() -> None:
	set_session_id('session-a')
	init()

	assert store_creator.get_content(WEBSOCKET_STORE, 'session-a') == {}

	destroy('session-a')


def test_set_websocket() -> None:
	websocket_mock = AsyncMock()

	anyio.run(set_websocket_in_event_loop, websocket_mock)

	assert store_creator.get_content(WEBSOCKET_STORE, resolve_local_id()).get(id(websocket_mock)).get('websocket') is websocket_mock


def test_delete_websocket() -> None:
	websocket_mock = AsyncMock()

	anyio.run(set_and_delete_websocket, websocket_mock)

	assert store_creator.get_content(WEBSOCKET_STORE, resolve_local_id()) == {}


def test_destroy() -> None:
	websocket_mock = AsyncMock()

	set_session_id('session-a')
	init()
	anyio.run(set_and_destroy_websocket, websocket_mock, 'session-a')

	websocket_mock.close.assert_awaited_once()
	assert store_creator.has_content(WEBSOCKET_STORE, 'session-a') is False
