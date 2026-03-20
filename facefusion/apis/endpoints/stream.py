import asyncio
import threading

import cv2
import numpy
from starlette.websockets import WebSocket

from facefusion import session_context, session_manager, state_manager
from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.apis.session_helper import extract_access_token
from facefusion.apis.stream_helper import STREAM_FPS, STREAM_QUALITY, close_stream_encoder, create_stream_encoder, encode_stream_frame, process_stream_frame, read_stream_output
from facefusion.streamer import process_vision_frame


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
				temp_vision_frame = process_vision_frame(target_vision_frame)
				is_success, output_vision_frame = cv2.imencode('.jpg', temp_vision_frame)

				if is_success:
					await websocket.send_bytes(output_vision_frame.tobytes())

		except Exception:
			pass
		return

	await websocket.close()


async def websocket_stream_live(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	access_token = extract_access_token(websocket.scope)
	session_id = session_manager.find_session_id(access_token)

	session_context.set_session_id(session_id)
	source_paths = state_manager.get_item('source_paths')

	await websocket.accept(subprotocol = subprotocol)

	if source_paths:
		encoder = None
		reader_thread = None
		output_chunks = []
		lock = threading.Lock()

		try:
			while True:
				image_buffer = await websocket.receive_bytes()
				target_vision_frame = cv2.imdecode(numpy.frombuffer(image_buffer, numpy.uint8), cv2.IMREAD_COLOR)

				if numpy.any(target_vision_frame):
					temp_vision_frame = await asyncio.get_running_loop().run_in_executor(None, process_stream_frame, target_vision_frame)

					if not encoder:
						height, width = temp_vision_frame.shape[:2]
						encoder = create_stream_encoder(width, height, STREAM_FPS, STREAM_QUALITY)
						reader_thread = threading.Thread(target = read_stream_output, args = (encoder, output_chunks, lock), daemon = True)
						reader_thread.start()

					encoded_bytes = encode_stream_frame(encoder, temp_vision_frame, output_chunks, lock)

					if encoded_bytes:
						await websocket.send_bytes(encoded_bytes)

		except Exception:
			pass

		if encoder:
			close_stream_encoder(encoder)
		return

	await websocket.close()
