import cv2
import numpy
from starlette.websockets import WebSocket, WebSocketDisconnect

from facefusion import session_context, session_manager, state_manager
from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.apis.endpoints.session import extract_access_token
from facefusion.streamer import process_stream_frame


async def websocket_process_image(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	access_token = extract_access_token(websocket.scope)
	session_id = session_manager.find_session_id(access_token)

	session_context.set_session_id(session_id)
	source_paths = state_manager.get_item('source_paths')

	await websocket.accept(subprotocol = subprotocol)

	if source_paths:
		try:
			while True:
				image_bytes = await websocket.receive_bytes()
				target_vision_frame = cv2.imdecode(numpy.frombuffer(image_bytes, numpy.uint8), cv2.IMREAD_COLOR)

				if numpy.any(target_vision_frame):
					temp_vision_frame = process_stream_frame(target_vision_frame)
					success, result_bytes = cv2.imencode('.jpg', temp_vision_frame)

					if success:
						await websocket.send_bytes(result_bytes.tobytes())

		except (WebSocketDisconnect, OSError):
			pass
		return

	await websocket.close(code = 1008)
