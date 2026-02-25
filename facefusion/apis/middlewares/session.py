from starlette.responses import JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_426_UPGRADE_REQUIRED
from starlette.types import ASGIApp, Receive, Scope, Send

from facefusion import session_manager, translator
from facefusion.apis.session_helper import extract_access_token


def create_session_guard(app : ASGIApp) -> ASGIApp:
	async def middleware(scope : Scope, receive : Receive, send : Send) -> None:
		access_token = extract_access_token(scope)

		if access_token:
			session_id = session_manager.find_session_id(access_token)

			if session_id:
				if session_manager.validate_session(session_id):
					return await app(scope, receive, send)

				response = JSONResponse(
				{
					'message': translator.get('invalid_access_token', 'facefusion.apis')
				}, status_code = HTTP_426_UPGRADE_REQUIRED)

				return await response(scope, receive, send)

		response = JSONResponse(
		{
			'message': translator.get('invalid_access_token', 'facefusion.apis')
		}, status_code = HTTP_401_UNAUTHORIZED)

		return await response(scope, receive, send)

	return middleware
