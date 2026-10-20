import asyncio

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_404_NOT_FOUND
from starlette.websockets import WebSocket

from facefusion.apis import websocket_manager
from facefusion.apis.websocket_helper import get_sec_websocket_protocol
from facefusion.system import get_metrics_set


async def get_metrics(request : Request) -> Response:
	metrics_set = get_metrics_set()

	if metrics_set:
		return JSONResponse(metrics_set)

	return Response(status_code = HTTP_404_NOT_FOUND)


async def websocket_metrics(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)

	if not websocket_manager.has_connection('metrics'):
		await websocket.accept(subprotocol = subprotocol)
		websocket_manager.start_connection('metrics', websocket)
		receive_task = asyncio.create_task(websocket.receive())

		while websocket_manager.has_connection('metrics') and not receive_task.done():
			metrics_set = get_metrics_set()

			await websocket.send_json(metrics_set)
			await asyncio.wait([ receive_task ], timeout = 2)

		receive_task.cancel()
		websocket_manager.end_connection('metrics', websocket)

	else:
		await websocket.close()
