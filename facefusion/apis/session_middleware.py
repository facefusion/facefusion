from typing import Optional

from starlette.datastructures import Headers
from starlette.responses import Response
from starlette.status import HTTP_401_UNAUTHORIZED
from starlette.types import ASGIApp, Receive, Scope, Send

from facefusion import session_manager
from facefusion.types import Token


def extract_access_token(headers : Headers) -> Optional[Token]:
	auth_header = headers.get('Authorization')

	if auth_header:
		_, _, access_token = auth_header.partition(' ')

		if access_token:
			return access_token

	return None



class SessionMiddleware:
	def __init__(self, app : ASGIApp) -> None:
		self.app = app

	async def __call__(self, scope : Scope, receive : Receive, send : Send) -> None:
		access_token = extract_access_token(Headers(scope = scope))

		if access_token and session_manager.validate_session(access_token):
			await self.app(scope, receive, send)
		else:
			if access_token:
				session = session_manager.get_session(access_token)

				if session:
					session_manager.clear_session(access_token)
					refresh_token = str(session.get('refresh_token'))

					if refresh_token in session_manager.SESSIONS:
						session_manager.clear_session(refresh_token)

			response = Response(status_code = HTTP_401_UNAUTHORIZED)
			await response(scope, receive, send)
