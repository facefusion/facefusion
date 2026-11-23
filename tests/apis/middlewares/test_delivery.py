from unittest.mock import AsyncMock

import pytest
from starlette.types import Scope

from facefusion.apis.middlewares.delivery import receive_with_event, send_with_event


@pytest.mark.asyncio
async def test_receive_with_event() -> None:
	scope : Scope = {}
	receive_mock = AsyncMock(return_value =
	{
		'type': 'websocket.disconnect'
	})

	assert await receive_with_event(scope, receive_mock) == { 'type': 'websocket.disconnect' }
	assert scope.get('client_event') == 'websocket.disconnect'


@pytest.mark.asyncio
async def test_send_with_event() -> None:
	scope : Scope = {}
	send_mock = AsyncMock()

	await send_with_event(scope, send_mock,
	{
		'type': 'websocket.send'
	})

	assert send_mock.await_count == 1

	scope['client_event'] = 'websocket.disconnect'
	await send_with_event(scope, send_mock,
	{
		'type': 'websocket.send'
	})

	assert send_mock.await_count == 1
