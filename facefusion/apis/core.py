import os

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles

from facefusion.apis.endpoints.assets import delete_assets, get_asset, get_assets, upload_asset
from facefusion.apis.endpoints.capabilities import get_capabilities
from facefusion.apis.endpoints.metrics import get_metrics, websocket_metrics
from facefusion.apis.endpoints.nodes import execute_node, list_nodes
from facefusion.apis.endpoints.ping import websocket_ping
from facefusion.apis.endpoints.session import create_session, destroy_session, get_session, refresh_session
from facefusion.apis.endpoints.state import get_state, set_state
from facefusion.apis.endpoints.stream import webrtc_stream, websocket_stream
from facefusion.apis.middlewares.session import create_session_guard


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
			Route('/assets', get_assets, methods = [ 'GET' ], middleware = [ session_guard ]),
			Route('/assets', upload_asset, methods = [ 'POST' ], middleware = [ session_guard ]),
			Route('/assets/{asset_id}', get_asset, methods = [ 'GET' ], middleware = [ session_guard ]),
			Route('/assets', delete_assets, methods = [ 'DELETE' ], middleware = [ session_guard ]),
			Route('/capabilities', get_capabilities, methods = [ 'GET' ]),
			Route('/nodes', list_nodes, methods = [ 'GET' ]),
			Route('/nodes/{node_name}', execute_node, methods = [ 'POST' ], middleware = [ session_guard ]),
			Route('/metrics', get_metrics, methods = [ 'GET' ], middleware = [ session_guard ]),
			Route('/stream', webrtc_stream, methods = ['POST'], middleware = [session_guard]),
			WebSocketRoute('/metrics', websocket_metrics, middleware = [ session_guard ]),
			WebSocketRoute('/ping', websocket_ping, middleware = [ session_guard ]),
			WebSocketRoute('/stream', websocket_stream, middleware = [session_guard])
		]

	static_path = os.path.join(os.path.dirname(__file__), 'static')
	routes.append(Mount('/', app = StaticFiles(directory = static_path, html = True)))

	api = Starlette(routes = routes)
	api.add_middleware(CORSMiddleware, allow_origins = [ '*' ], allow_methods = [ '*' ], allow_headers = [ '*' ])

	return api
