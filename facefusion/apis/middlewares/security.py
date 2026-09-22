from functools import partial

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


async def send_with_security(send : Send, message : Message) -> None:
	if message.get('type') == 'http.response.start':
		MutableHeaders(scope = message).update(
		{
			'X-Content-Type-Options': 'nosniff',
			'X-Frame-Options': 'DENY',
			'Content-Security-Policy': "frame-ancestors 'none'",
			'Referrer-Policy': 'no-referrer',
			'Cache-Control': 'no-store'
		})

	await send(message)


def create_security_guard(app : ASGIApp) -> ASGIApp:
	async def middleware(scope : Scope, receive : Receive, send : Send) -> None:
		if scope.get('type') == 'http':
			return await app(scope, receive, partial(send_with_security, send))

		return await app(scope, receive, send)

	return middleware
