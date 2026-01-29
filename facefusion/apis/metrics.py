import asyncio

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_404_NOT_FOUND
from starlette.websockets import WebSocket

from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.system import get_metrics_set


async def get_metrics(request : Request) -> Response:
	metrics_set = get_metrics_set()

	if metrics_set:
		return JSONResponse(metrics_set)

	return Response(status_code = HTTP_404_NOT_FOUND)


async def websocket_metrics(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	await websocket.accept(subprotocol = subprotocol)

	try:
		while True:
			metrics_set = get_metrics_set()
			await websocket.send_json(metrics_set)
			await asyncio.sleep(2)

	except Exception:
		pass
