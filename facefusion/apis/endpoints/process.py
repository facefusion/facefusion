import asyncio

from starlette.websockets import WebSocket

from facefusion import process_manager
from facefusion.apis import websocket_manager
from facefusion.apis.websocket_helper import get_sec_websocket_protocol


async def websocket_process(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)

	if not websocket_manager.has_connection('process'):
		await websocket.accept(subprotocol = subprotocol)
		websocket_manager.start_connection('process', websocket)
		receive_task = asyncio.create_task(websocket.receive())

		while websocket_manager.has_connection('process') and not receive_task.done():
			process_state = process_manager.get_state()

			await websocket.send_text(process_state)
			await asyncio.wait([ receive_task ], timeout = 0.5)

		receive_task.cancel()
		websocket_manager.end_connection('process', websocket)

	else:
		await websocket.close()
