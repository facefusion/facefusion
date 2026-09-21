from json import JSONDecodeError

from starlette.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST
from starlette.types import ASGIApp, Receive, Scope, Send

from facefusion import translator


def create_exception_guard(app : ASGIApp) -> ASGIApp:
	async def middleware(scope : Scope, receive : Receive, send : Send) -> None:
		try:
			await app(scope, receive, send)
		except JSONDecodeError:
			response = JSONResponse(
			{
				'message': translator.get('something_went_wrong', 'facefusion.apis')
			}, status_code = HTTP_400_BAD_REQUEST)

			await response(scope, receive, send)

	return middleware
