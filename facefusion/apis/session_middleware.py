from datetime import datetime
from typing import Optional

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED
from starlette.types import ASGIApp, Receive, Scope, Send

from facefusion import session_manager
from facefusion.types import Token


def extract_access_token(headers : Headers) -> Optional[Token]:
	auth_header = headers.get('Authorization')

	if not auth_header:
		return None
	parts = auth_header.split(' ', 1)

	token = parts[1] if len(parts) == 2 else parts[0]
	session_data = session_manager.get_session(token)
	if not session_data:
		return None

	if datetime.now() > session_data.get('expires_at'):
		session_manager.clear_session(token)
		if str(session_data.get('refresh_token')) in session_manager.SESSIONS:
			session_manager.clear_session(str(session_data.get('refresh_token')))
		return None
	return token


class SessionMiddleware:
	def __init__(self, app : ASGIApp) -> None:
		self.app = app

	async def __call__(self, scope : Scope, receive : Receive, send : Send) -> None:
		headers = Headers(scope = scope)
		token = extract_access_token(headers)

		if token:
			await self.app(scope, receive, send)
			return

		response = JSONResponse({ "error": { "message": "Missing Authorization header" } }, status_code = HTTP_401_UNAUTHORIZED)
		await response(scope, receive, send)
