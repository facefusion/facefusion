from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route

from facefusion.apis.session import create_session
from facefusion.apis.session import create_session_guard
from facefusion.apis.session import destroy_session
from facefusion.apis.session import get_session
from facefusion.apis.session import refresh_session
from facefusion.apis.state import get_state
from facefusion.apis.state import set_state


def create_api() -> Starlette:
	session_guard = Middleware(create_session_guard)
	routes =\
	[
		Route('/session', create_session, methods = [ 'POST' ]),
		Route('/session', get_session, methods = [ 'GET' ], middleware = [ session_guard ]),
		Route('/session', refresh_session, methods = [ 'PUT' ]),
		Route('/session', destroy_session, methods = [ 'DELETE' ], middleware = [ session_guard ]),
		Route('/state', get_state, methods = [ 'GET' ], middleware = [ session_guard ]),
		Route('/state', set_state, methods = [ 'PUT' ], middleware = [ session_guard ])
	]

	api = Starlette(routes = routes)
	api.add_middleware(CORSMiddleware, allow_origins = [ '*' ], allow_methods = [ '*' ], allow_headers = [ '*' ])

	return api
