import asyncio

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_404_NOT_FOUND
from starlette.websockets import WebSocket

from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.system import get_metrics


async def metrics(request : Request) -> Response:
	metrics_data = get_metrics()

	if metrics_data:
		return JSONResponse(metrics_data)

	return Response(status_code = HTTP_404_NOT_FOUND)


async def websocket_metrics(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	await websocket.accept(subprotocol = subprotocol)

	try:
		while True:
			metrics_data = get_metrics()
			await websocket.send_json(metrics_data)
			await asyncio.sleep(2)

	except Exception:
		pass
