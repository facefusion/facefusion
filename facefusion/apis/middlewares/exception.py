from json import JSONDecodeError

from python_multipart.exceptions import MultipartParseError
from starlette.requests import ClientDisconnect
from starlette.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.websockets import WebSocketDisconnect

from facefusion import translator


def create_exception_guard(app : ASGIApp) -> ASGIApp:
	async def middleware(scope : Scope, receive : Receive, send : Send) -> None:
		if scope.get('type') == 'http':
			try:
				return await app(scope, receive, send)
			except (JSONDecodeError, MultipartParseError, UnicodeDecodeError):
				response = JSONResponse(
				{
					'message': translator.get('something_went_wrong', 'facefusion.apis')
				}, status_code = HTTP_400_BAD_REQUEST)

				return await response(scope, receive, send)
			except ClientDisconnect:
				return

		if scope.get('type') == 'websocket':
			try:
				return await app(scope, receive, send)
			except WebSocketDisconnect:
				return

		return await app(scope, receive, send)

	return middleware
