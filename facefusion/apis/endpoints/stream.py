from functools import partial

import cv2
import numpy
from aiortc import RTCPeerConnection, RTCSessionDescription
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from starlette.websockets import WebSocket

from facefusion import session_context, session_manager, state_manager
from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.apis.session_helper import extract_access_token
from facefusion.apis.stream_helper import on_video_track
from facefusion.streamer import process_stream_frame


async def websocket_stream(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	access_token = extract_access_token(websocket.scope)
	session_id = session_manager.find_session_id(access_token)

	session_context.set_session_id(session_id)
	source_paths = state_manager.get_item('source_paths')

	await websocket.accept(subprotocol = subprotocol)

	if source_paths:
		try:
			image_buffer = await websocket.receive_bytes()
			target_vision_frame = cv2.imdecode(numpy.frombuffer(image_buffer, numpy.uint8), cv2.IMREAD_COLOR)

			if numpy.any(target_vision_frame):
				temp_vision_frame = process_stream_frame(target_vision_frame)
				is_success, output_vision_frame = cv2.imencode('.jpg', temp_vision_frame)

				if is_success:
					await websocket.send_bytes(output_vision_frame.tobytes())

		except Exception:
			pass
		return

	await websocket.close()


async def webrtc_stream(request : Request) -> Response:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)
	session_context.set_session_id(session_id)

	if session_id:
		body = await request.json()
		rtc_offer = RTCSessionDescription(sdp = body.get('sdp'), type = body.get('type'))
		rtc_connection = RTCPeerConnection()

		rtc_connection.on('track', partial(on_video_track, rtc_connection))

		await rtc_connection.setRemoteDescription(rtc_offer)
		await rtc_connection.setLocalDescription(await rtc_connection.createAnswer())

		return JSONResponse(
		{
			'sdp': rtc_connection.localDescription.sdp,
			'type': rtc_connection.localDescription.type
		})

	return Response(status_code = HTTP_500_INTERNAL_SERVER_ERROR)
