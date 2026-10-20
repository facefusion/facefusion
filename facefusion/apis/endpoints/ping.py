from starlette.websockets import WebSocket, WebSocketState

from facefusion.apis import websocket_manager
from facefusion.apis.websocket_helper import get_sec_websocket_protocol


async def websocket_ping(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)

	if not websocket_manager.has_connection('ping'):
		await websocket.accept(subprotocol = subprotocol)
		websocket_manager.start_connection('ping', websocket)

		while websocket_manager.has_connection('ping') and websocket.client_state == WebSocketState.CONNECTED:
			await websocket.receive()

		websocket_manager.end_connection('ping', websocket)

	else:
		await websocket.close()
