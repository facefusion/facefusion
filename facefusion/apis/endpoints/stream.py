from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND
from starlette.websockets import WebSocket

from facefusion import session_context, session_manager
from facefusion.apis.session_helper import extract_access_token
from facefusion.apis.stream_helper import add_rtc_viewer, handle_image_stream, handle_video_stream


async def websocket_stream(websocket : WebSocket) -> None:
	stream_mode = websocket.query_params.get('mode')

	if stream_mode == 'image':
		return await handle_image_stream(websocket)

	if stream_mode == 'video':
		return await handle_video_stream(websocket)

	return await websocket.close(1008)


async def post_stream(request : Request) -> Response:
	content_type = request.headers.get('content-type')
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)
	session_context.set_session_id(session_id)

	if content_type == 'application/sdp' and session_id:
		sdp_offer = await request.body()
		sdp_answer = add_rtc_viewer(session_id, sdp_offer.decode())

		if sdp_answer:
			return Response(sdp_answer, status_code = HTTP_201_CREATED, media_type = 'application/sdp')

	return Response(status_code = HTTP_404_NOT_FOUND)
