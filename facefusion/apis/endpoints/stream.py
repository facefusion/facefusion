from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND
from starlette.websockets import WebSocket

from facefusion import session_context, session_manager
from facefusion.apis.session_helper import extract_access_token
from facefusion.apis.stream_helper import destroy_stream, process_image, process_video


async def websocket_stream(websocket : WebSocket) -> None:
	return await process_image(websocket)


async def post_stream(request : Request) -> Response:
	content_type = request.headers.get('content-type')
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)

	session_context.set_session_id(session_id)

	if session_id and content_type == 'application/sdp':
		sdp_offer = await request.body()
		sdp_answer = process_video(session_id, sdp_offer.decode())

		if sdp_answer:
			return Response(sdp_answer, status_code = HTTP_201_CREATED, media_type = 'application/sdp')

	return Response(status_code = HTTP_404_NOT_FOUND)


async def delete_stream(request : Request) -> Response:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)

	if session_id and destroy_stream(session_id):
		return Response(status_code = HTTP_200_OK)

	return Response(status_code = HTTP_404_NOT_FOUND)
