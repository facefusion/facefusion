from functools import partial

from starlette.types import ASGIApp, Message, Receive, Scope, Send


async def receive_with_event(scope : Scope, receive : Receive) -> Message:
	message = await receive()
	scope['client_event'] = message.get('type')
	return message


async def send_with_event(scope : Scope, send : Send, message : Message) -> None:
	if not scope.get('client_event') == 'websocket.disconnect':
		await send(message)


def create_delivery_guard(app : ASGIApp) -> ASGIApp:
	async def middleware(scope : Scope, receive : Receive, send : Send) -> None:
		if scope.get('type') == 'websocket':
			return await app(scope, partial(receive_with_event, scope, receive), partial(send_with_event, scope, send))

		return await app(scope, receive, send)

	return middleware
