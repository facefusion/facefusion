import asyncio

from starlette.websockets import WebSocket

from facefusion import process_manager
from facefusion.apis import websocket_manager
from facefusion.apis.websocket_helper import get_sec_websocket_protocol
from facefusion.session_manager import find_fork_session_id, resolve_owner_id
from facefusion.types import ProcessSet


async def websocket_process(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)

	if not websocket_manager.has_connection('process'):
		await websocket.accept(subprotocol = subprotocol)
		websocket_manager.start_connection('process', websocket)
		receive_task = asyncio.create_task(websocket.receive())

		while websocket_manager.has_connection('process') and not receive_task.done():
			owner_id = resolve_owner_id()
			fork_id = find_fork_session_id(owner_id)
			process_set : ProcessSet =\
			{
				'session': process_manager.get_process(owner_id)
			}

			if fork_id and process_manager.has_process(fork_id):
				process_set['fork'] = process_manager.get_process(fork_id)

			await websocket.send_json(process_set)
			await asyncio.wait([ receive_task ], timeout = 0.5)

		receive_task.cancel()
		websocket_manager.end_connection('process', websocket)

	else:
		await websocket.close()
