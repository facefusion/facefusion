from starlette.websockets import WebSocket

from facefusion.apis import websocket_manager
from facefusion.apis.websocket_helper import get_sec_websocket_protocol


async def websocket_ping(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)

	if not websocket_manager.has_connection('ping'):
		await websocket.accept(subprotocol = subprotocol)
		websocket_manager.start_connection('ping', websocket)

		try:
			while True:
				await websocket.receive()

		except Exception:
			pass

		websocket_manager.end_connection('ping')

	else:
		await websocket.close()
