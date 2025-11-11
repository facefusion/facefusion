import time
from typing import Awaitable
from typing import Callable
from typing import Dict
from typing import TypeAlias

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.status import HTTP_401_UNAUTHORIZED
from starlette.types import ASGIApp
from starlette.types import Receive
from starlette.types import Scope
from starlette.types import Send

from facefusion import session_manager


JSON : TypeAlias = Dict[str, object]


def error_response(message : str) -> Response:
	return JSONResponse({ "error": { "code": "UNAUTHORIZED", "message": message, "details": {} } }, status_code = HTTP_401_UNAUTHORIZED)


def validate_bearer_token(headers : Headers) -> str:
	auth_header = headers.get('Authorization', '')
	if not auth_header:
		raise ValueError('Missing Authorization header')
	parts = auth_header.split(' ', 1)
	if len(parts) != 2 or parts[0].lower() != 'bearer':
		raise ValueError('Invalid Authorization header format')
	token = parts[1]
	session_data = session_manager.get_session(token)
	if not session_data:
		raise ValueError('Invalid or expired token')
	if int(time.time()) > int(session_data.get('expires_at')):
		session_manager.clear_session(token)
		session_manager.clear_session(str(session_data.get('refresh_token')))
		raise ValueError('Token expired')
	return token


class SessionMiddleware:
	def __init__(self, app : ASGIApp) -> None:
		self.app = app

	async def __call__(self, scope : Scope, receive : Receive, send : Send) -> None:
		if scope['type'] != 'http':
			await self.app(scope, receive, send)
			return
		headers = Headers(scope=scope)
		try:
			token = validate_bearer_token(headers)
			scope['auth_token'] = token
			await self.app(scope, receive, send)
		except ValueError as e:
			response = error_response(str(e))
			await response(scope, receive, send)
