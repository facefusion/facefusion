from functools import partial
from typing import List

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from facefusion import logger


def create_logger(app : ASGIApp) -> ASGIApp:
	async def middleware(scope : Scope, receive : Receive, send : Send) -> None:
		if scope.get('type') == 'http':
			status_codes : List[int] = []
			await app(scope, receive, partial(capture_status_code, send, status_codes))

			for status_code in status_codes:
				logger.info(str(scope.get('method')).lower() + ' ' + str(scope.get('path')) + ' ' + str(status_code), 'facefusion.apis.request')

			return None

		return await app(scope, receive, send)

	return middleware


async def capture_status_code(send : Send, status_codes : List[int], message : Message) -> None:
	if message.get('type') == 'http.response.start':
		status_codes.append(message.get('status'))

	await send(message)
