from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route, WebSocketRoute

from facefusion.apis.choices import get_choices
from facefusion.apis.endpoints.assets import delete_asset, delete_assets, get_asset, get_assets, upload_asset
from facefusion.apis.endpoints.ping import websocket_ping
from facefusion.apis.endpoints.session import create_session, create_session_guard, destroy_session, get_session, refresh_session
from facefusion.apis.endpoints.state import get_state, set_state
from facefusion.apis.metrics import websocket_metrics
from facefusion.apis.process import webrtc_offer, webrtc_stream_offer, websocket_process
from facefusion.apis.remote import remote
from facefusion.apis.timeline import get_timeline
from facefusion.apis.version import create_version_guard


def create_api() -> Starlette:
	version_guard = Middleware(create_version_guard)
	session_guard = Middleware(create_session_guard)
	routes =\
	[
		Route('/session', create_session, methods = [ 'POST' ], middleware = [ version_guard ]),
		Route('/session', get_session, methods = [ 'GET' ], middleware = [ version_guard, session_guard ]),
		Route('/session', refresh_session, methods = [ 'PUT' ], middleware = [ version_guard ]),
		Route('/session', destroy_session, methods = [ 'DELETE' ], middleware = [ version_guard, session_guard ]),
		Route('/state', get_state, methods = [ 'GET' ], middleware = [ version_guard, session_guard ]),
		Route('/state', set_state, methods = [ 'PUT' ], middleware = [ version_guard, session_guard ]),
		Route('/assets', get_assets, methods = [ 'GET' ], middleware = [ version_guard, session_guard ]),
		Route('/assets', upload_asset, methods = [ 'POST' ], middleware = [ version_guard, session_guard ]),
		Route('/assets/{asset_id}', get_asset, methods = [ 'GET' ], middleware = [ version_guard, session_guard ]),
		Route('/assets/{asset_id}', delete_asset, methods = [ 'DELETE' ], middleware = [ version_guard, session_guard ]),
		Route('/assets', delete_assets, methods = [ 'DELETE' ], middleware = [ version_guard, session_guard ]),
		Route('/choices', get_choices, methods = [ 'GET' ], middleware = [ version_guard, session_guard ]),
		Route('/remote', remote, methods = [ 'POST' ], middleware = [ version_guard, session_guard ]),
		Route('/timeline/{count:int}', get_timeline, methods = [ 'GET' ], middleware = [ version_guard, session_guard ]),
		Route('/webrtc/offer', webrtc_offer, methods = [ 'POST' ], middleware = [ version_guard, session_guard ]),
		Route('/stream/webrtc/offer', webrtc_stream_offer, methods = [ 'POST' ], middleware = [ version_guard, session_guard ]),
		WebSocketRoute('/metrics', websocket_metrics, middleware = [ version_guard, session_guard ]),
		WebSocketRoute('/ping', websocket_ping, middleware = [ version_guard, session_guard ]),
		WebSocketRoute('/process', websocket_process, middleware = [ version_guard, session_guard ])
	]

	api = Starlette(routes = routes)
	api.add_middleware(CORSMiddleware, allow_origins = [ '*' ], allow_methods = [ '*' ], allow_headers = [ '*' ])

	return api
