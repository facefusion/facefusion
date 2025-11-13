import time
from typing import Optional
from typing import TypeAlias

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED
from starlette.types import ASGIApp
from starlette.types import Receive
from starlette.types import Scope
from starlette.types import Send

from facefusion import session_manager
# from facefusion import translator


Token : TypeAlias = str


def extract_access_token(headers : Headers) -> Optional[Token]:
	auth_header = headers.get('Authorization', '')
	if not auth_header:
		return None
	parts = auth_header.split(' ', 1)
	# if len(parts) != 2:
	# 	return None
	# if parts[0].lower() != 'bearer':
	# 	return None
	token = parts[1] if len(parts) == 2 else parts[0]
	session_data = session_manager.get_session(token)
	if not session_data:
		return None
	# Check if token matches
	# if session_data.get('token') != token:
	# 	return None
	if int(time.time()) > int(session_data.get('expires_at')):
		session_manager.clear_session(token)
		if str(session_data.get('refresh_token')) in session_manager.SESSIONS:
			session_manager.clear_session(str(session_data.get('refresh_token')))
		return None
	return token


class SessionMiddleware:
	def __init__(self, app : ASGIApp) -> None:
		self.app = app

	async def __call__(self, scope : Scope, receive : Receive, send : Send) -> None:
		# if scope['type'] != 'http':
		# 	await self.app(scope, receive, send)
		# 	return

		headers = Headers(scope = scope)
		token = extract_access_token(headers)

		if token:
			# scope['auth_token'] = token
			await self.app(scope, receive, send)
			return

		# if headers.get('Authorization', ''):
		# 	# message = translator.get('errors.invalid_or_expired', __package__) or 'Invalid or expired token'
		# 	# message = 'Invalid or expired token'
		# 	response = JSONResponse({ "error": { "message": "Invalid or expired token" } }, status_code = HTTP_401_UNAUTHORIZED)
		# 	await response(scope, receive, send)
		# 	return

		# message = translator.get('errors.missing_auth', __package__) or 'Missing Authorization header'
		# message = 'Missing Authorization header'
		response = JSONResponse({ "error": { "message": "Missing Authorization header" } }, status_code = HTTP_401_UNAUTHORIZED)
		await response(scope, receive, send)
