from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND
from starlette.websockets import WebSocket

from facefusion import session_context, session_manager
from facefusion.apis.session_helper import extract_access_token
from facefusion.apis.stream_helper import receive_video, send_video, process_image


async def websocket_stream(websocket : WebSocket) -> None:
	stream_type = websocket.query_params.get('type')
	stream_action = websocket.query_params.get('action')

	if stream_type == 'image' and stream_action == 'process':
		return await process_image(websocket)

	return await websocket.close(1008)


async def post_stream(request : Request) -> Response:
	content_type = request.headers.get('content-type')
	stream_type = request.query_params.get('type')
	stream_action = request.query_params.get('action')
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)

	session_context.set_session_id(session_id)

	if content_type == 'application/sdp' and session_id:
		sdp_offer = await request.body()

		if stream_type == 'video' and stream_action == 'receive':
			codec = request.query_params.get('codec', 'av1')
			sdp_answer = receive_video(session_id, sdp_offer.decode(), codec)

			return Response(sdp_answer, status_code = HTTP_201_CREATED, media_type='application/sdp')

		if stream_type == 'video' and stream_action == 'send':
			sdp_answer = send_video(session_id, sdp_offer.decode())

			return Response(sdp_answer, status_code = HTTP_201_CREATED, media_type = 'application/sdp')

	return Response(status_code = HTTP_404_NOT_FOUND)
