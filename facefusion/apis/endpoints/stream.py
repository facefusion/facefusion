from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from starlette.websockets import WebSocket, WebSocketState

from facefusion import rtc_store
from facefusion.apis import websocket_store
from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.apis.stream_manager import destroy_stream, process_image, process_video


async def websocket_stream(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)

	await websocket.accept(subprotocol = subprotocol)
	websocket_store.set_websocket(websocket)
	await process_image(websocket)
	websocket_store.delete_websocket(websocket)

	if websocket.client_state == WebSocketState.CONNECTED:
		await websocket.close()


async def post_stream(request : Request) -> Response:
	headers =\
	{
		'Location': request.url_for('delete_stream').path
	}
	if not rtc_store.has_peer():
		sdp_offer = await request.body()
		sdp_answer = process_video(sdp_offer.decode())

		if sdp_answer:
			return Response(sdp_answer, status_code = HTTP_201_CREATED, media_type = 'application/sdp', headers = headers)

	else:
		return Response(status_code = HTTP_409_CONFLICT)

	return Response(status_code = HTTP_404_NOT_FOUND)


async def delete_stream(request : Request) -> Response:
	if destroy_stream():
		return Response(status_code = HTTP_200_OK)

	return Response(status_code = HTTP_404_NOT_FOUND)
