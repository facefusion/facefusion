from contextlib import asynccontextmanager
from typing import AsyncGenerator

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route, WebSocketRoute

from facefusion import logger, mediamtx
from facefusion.apis.endpoints.assets import delete_assets, get_asset, get_assets, upload_asset
from facefusion.apis.endpoints.capabilities import get_capabilities
from facefusion.apis.endpoints.metrics import get_metrics, websocket_metrics
from facefusion.apis.endpoints.ping import websocket_ping
from facefusion.apis.endpoints.session import create_session, destroy_session, get_session, refresh_session
from facefusion.apis.endpoints.state import get_state, set_state
from facefusion.common_helper import is_linux, is_windows
from facefusion.apis.endpoints.stream import websocket_stream, websocket_stream_audio, websocket_stream_live, websocket_stream_mjpeg, websocket_stream_rtc, websocket_stream_rtc_relay, websocket_stream_whip, websocket_stream_whip_dc, websocket_stream_whip_py
from facefusion.apis.middlewares.session import create_session_guard


@asynccontextmanager
async def lifespan(app : Starlette) -> AsyncGenerator[None, None]:
	if is_linux():
		mediamtx.start()
		mediamtx.wait_for_ready()

	try:
		from facefusion import webrtc_sfu
		webrtc_sfu.start()
	except Exception as exception:
		logger.warn('webrtc sfu: ' + str(exception), __name__)

	try:
		from facefusion import whip_relay
		whip_relay.start()
		whip_relay.wait_for_ready()
	except Exception as exception:
		logger.warn('whip relay: ' + str(exception), __name__)

	try:
		from facefusion import rtc
		rtc.start()
	except Exception as exception:
		logger.warn('rtc: ' + str(exception), __name__)

	yield

	if is_linux():
		mediamtx.stop()

	try:
		from facefusion import webrtc_sfu
		webrtc_sfu.stop()
	except Exception:
		pass

	try:
		from facefusion import whip_relay
		whip_relay.stop()
	except Exception:
		pass

	try:
		from facefusion import rtc
		rtc.stop()
	except Exception:
		pass


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
			Route('/metrics', get_metrics, methods = [ 'GET' ], middleware = [ session_guard ]),
			WebSocketRoute('/metrics', websocket_metrics, middleware = [ session_guard ]),
			WebSocketRoute('/ping', websocket_ping, middleware = [ session_guard ]),
			WebSocketRoute('/stream', websocket_stream, middleware = [ session_guard ]),
			WebSocketRoute('/stream/whip', websocket_stream_whip, middleware = [ session_guard ]),
			WebSocketRoute('/stream/whip-py', websocket_stream_whip_py, middleware = [ session_guard ]),
			WebSocketRoute('/stream/whip-dc', websocket_stream_whip_dc, middleware = [ session_guard ]),
			WebSocketRoute('/stream/live', websocket_stream_live, middleware = [ session_guard ]),
			WebSocketRoute('/stream/rtc', websocket_stream_rtc, middleware = [ session_guard ]),
			WebSocketRoute('/stream/rtc-relay', websocket_stream_rtc_relay, middleware = [ session_guard ]),
			WebSocketRoute('/stream/mjpeg', websocket_stream_mjpeg, middleware = [ session_guard ]),
			WebSocketRoute('/stream/audio', websocket_stream_audio, middleware = [ session_guard ])
		]

	api = Starlette(routes = routes, lifespan = lifespan)
	api.add_middleware(CORSMiddleware, allow_origins = [ '*' ], allow_methods = [ '*' ], allow_headers = [ '*' ])

	return api
