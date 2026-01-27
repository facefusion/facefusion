import asyncio
from typing import Optional

from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

from facefusion.system import get_metrics


async def metrics(request : Request) -> JSONResponse:
	metrics_data = get_metrics()
	return JSONResponse(metrics_data)


async def websocket_metrics(websocket : WebSocket) -> None:
	subprotocol = get_requested_subprotocol(websocket)
	await websocket.accept(subprotocol = subprotocol)

	try:
		while True:
			metrics_data = get_metrics()
			await websocket.send_json(metrics_data)
			await asyncio.sleep(2)

	except (WebSocketDisconnect, Exception):
		pass


def get_requested_subprotocol(websocket : WebSocket) -> Optional[str]:
	headers = Headers(scope = websocket.scope)
	protocol_header = headers.get('Sec-WebSocket-Protocol')

	if protocol_header:
		protocol, _, _ = protocol_header.partition(',')
		return protocol.strip()

	return None
