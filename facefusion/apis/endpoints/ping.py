from starlette.websockets import WebSocket

from facefusion.apis.api_helper import get_sec_websocket_protocol


async def websocket_ping(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)

	await websocket.accept(subprotocol = subprotocol)

	try:
		while True:
			await websocket.receive()

	except Exception:
		pass
