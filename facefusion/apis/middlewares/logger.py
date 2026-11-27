from functools import partial

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from facefusion import logger


def create_logger(app : ASGIApp) -> ASGIApp:
	async def middleware(scope : Scope, receive : Receive, send : Send) -> None:
		if scope.get('type') == 'http':
			return await app(scope, receive, partial(send_with_log, scope, send))

		return await app(scope, receive, send)

	return middleware


async def send_with_log(scope : Scope, send : Send, message : Message) -> None:
	if message.get('type') == 'http.response.start':
		logger.info(scope.get('method') + ' ' + scope.get('path') + ' ' + str(message.get('status')), 'facefusion.apis.request')

	await send(message)
