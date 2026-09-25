from starlette.websockets import WebSocket

from facefusion.apis import websocket_store
from facefusion.apis.api_helper import get_sec_websocket_protocol


async def websocket_ping(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)

	await websocket.accept(subprotocol = subprotocol)
	websocket_store.set_websocket(websocket)

	try:
		while True:
			await websocket.receive()

	except Exception:
		pass

	websocket_store.delete_websocket(websocket)
