from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from starlette.status import HTTP_204_NO_CONTENT

from facefusion.apis.session import create_session
from facefusion.apis.session import destroy_session
from facefusion.apis.session import get_session
from facefusion.apis.session import refresh_session
from facefusion.apis.state import get_state
from facefusion.apis.session_middleware import SessionMiddleware


async def root(request : Request) -> Response:
	return Response(status_code = HTTP_204_NO_CONTENT)


def create_api() -> Starlette:
	routes =\
	[
		Route('/', root),
		Route('/session', create_session, methods = [ 'POST' ]),
		Route('/session', get_session, methods = [ 'GET' ], middleware = [ Middleware(SessionMiddleware) ]),
		Route('/session', refresh_session, methods = [ 'PUT' ]),
		Route('/session', destroy_session, methods = [ 'DELETE' ], middleware = [ Middleware(SessionMiddleware) ]),
		Route('/state', get_state, methods = [ 'GET' ], middleware = [ Middleware(SessionMiddleware) ])
	]

	api = Starlette(routes = routes)
	api.add_middleware(CORSMiddleware, allow_origins = [ '*' ], allow_methods = [ '*' ], allow_headers = [ '*' ])

	return api
