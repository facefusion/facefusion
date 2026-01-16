from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route, WebSocketRoute

from facefusion.apis.endpoints.assets import upload_asset
from facefusion.apis.endpoints.ping import websocket_ping
from facefusion.apis.endpoints.session import create_session, create_session_guard, destroy_session, get_session, refresh_session
from facefusion.apis.endpoints.state import get_state, set_state


def create_api() -> Starlette:
	session_guard = Middleware(create_session_guard)
	routes =\
		[
			Route('/session', create_session, methods = [ 'POST' ]),
			Route('/session', get_session, methods = [ 'GET' ], middleware = [ session_guard ]),
			Route('/session', refresh_session, methods = [ 'PUT' ]),
			Route('/session', destroy_session, methods = [ 'DELETE' ], middleware = [ session_guard ]),
			Route('/state', get_state, methods = [ 'GET' ], middleware = [ session_guard ]),
			Route('/state', set_state, methods = [ 'PUT' ], middleware = [ session_guard ]),
			Route('/assets', upload_asset, methods = [ 'POST' ], middleware = [ session_guard ]),
			WebSocketRoute('/ping', websocket_ping, middleware = [ session_guard ])
		]

	api = Starlette(routes = routes)
	api.add_middleware(CORSMiddleware, allow_origins = [ '*' ], allow_methods = [ '*' ], allow_headers = [ '*' ])

	return api
