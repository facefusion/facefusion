import asyncio
import subprocess
import threading
import time
from collections import deque
from collections.abc import AsyncIterator

import cv2
import numpy
from starlette.requests import Request
from starlette.responses import Response
from starlette.websockets import WebSocket, WebSocketState

from facefusion import rtc_store, session_context, session_manager, state_manager
from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.apis.session_helper import extract_access_token
from facefusion.apis.stream_helper import calculate_bitrate, calculate_buffer_size, forward_stream_frame, get_websocket_stream_mode, is_jpeg_buffer
from facefusion.ffmpeg import spawn_stream
from facefusion.streamer import process_vision_frame
from facefusion.types import SessionId, VisionFrame


async def receive_vision_frames(websocket : WebSocket) -> AsyncIterator[VisionFrame]:
	websocket_event = await websocket.receive()

	while websocket_event.get('type') == 'websocket.receive':
		frame_buffer = websocket_event.get('bytes') or b''

		if is_jpeg_buffer(frame_buffer):
			vision_frame = cv2.imdecode(numpy.frombuffer(frame_buffer, numpy.uint8), cv2.IMREAD_COLOR)

			if numpy.any(vision_frame):
				yield vision_frame

		websocket_event = await websocket.receive()


def forward_rtc_frames(encoder : subprocess.Popen[bytes], session_id : SessionId) -> None:
	for stream_buffer in forward_stream_frame(encoder):
		rtc_store.send_rtc_frame(session_id, stream_buffer)


async def handle_image_stream(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	access_token = extract_access_token(websocket.scope)
	session_id = session_manager.find_session_id(access_token)
	session_context.set_session_id(session_id)
	source_paths = state_manager.get_item('source_paths')

	await websocket.accept(subprotocol = subprotocol)

	if source_paths:
		capture_vision_frame = await anext(receive_vision_frames(websocket), None)

		if numpy.any(capture_vision_frame):
			output_vision_frame = process_vision_frame(capture_vision_frame)
			is_success, output_frame_buffer = cv2.imencode('.jpg', output_vision_frame)

			if is_success:
				await websocket.send_bytes(output_frame_buffer.tobytes())

	if websocket.client_state == WebSocketState.CONNECTED:
		await websocket.close()


async def handle_video_stream(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	access_token = extract_access_token(websocket.scope)
	session_id = session_manager.find_session_id(access_token)
	session_context.set_session_id(session_id)
	source_paths = state_manager.get_item('source_paths')

	await websocket.accept(subprotocol = subprotocol)

	if session_id and source_paths:
		output_video_fps = int(state_manager.get_item('output_video_fps') or 30) # TODO: resolve from target video fps
		vision_frames = receive_vision_frames(websocket)
		vision_frame = await anext(vision_frames, None)

		if numpy.any(vision_frame):
			resolution = (vision_frame.shape[1], vision_frame.shape[0])
			encoder = spawn_stream(resolution, output_video_fps, calculate_bitrate(resolution), calculate_buffer_size(resolution))

			vision_frame_deque : deque[VisionFrame] = deque(maxlen = 1)
			encode_frame_deque : deque[VisionFrame] = deque()

			vision_frame_deque.append(vision_frame)
			rtc_store.create_rtc_stream(session_id)
			threading.Thread(target = forward_rtc_frames, args = (encoder, session_id), daemon = True).start()

			loop = asyncio.get_running_loop()
			await loop.run_in_executor(None, submit_encoder_frame, encoder, vision_frame_deque, encode_frame_deque)
			await websocket.send_text('ready')
			pipeline_task = loop.run_in_executor(None, run_encode_loop, encoder, vision_frame_deque, encode_frame_deque)

			async for vision_frame in vision_frames:
				vision_frame_deque.append(vision_frame)

			vision_frame_deque.clear()
			encoder.stdin.close()
			await pipeline_task
			rtc_store.destroy_rtc_stream(session_id)

	if websocket.client_state == WebSocketState.CONNECTED:
		await websocket.close()


def submit_encoder_frame(encoder : subprocess.Popen[bytes], vision_frame_deque : deque[VisionFrame], encode_frame_deque : deque[VisionFrame]) -> None:
	output_vision_frame = process_vision_frame(vision_frame_deque[-1])
	encode_frame_deque.append(output_vision_frame)
	encoder.stdin.write(cv2.cvtColor(output_vision_frame, cv2.COLOR_BGR2RGB).tobytes())
	encoder.stdin.flush()


def run_encode_loop(encoder : subprocess.Popen[bytes], vision_frame_deque : deque[VisionFrame], encode_frame_deque : deque[VisionFrame]) -> None:
	while encoder.poll() is None:

		if vision_frame_deque and not encoder.stdin.closed:
			submit_encoder_frame(encoder, vision_frame_deque, encode_frame_deque)
			continue

		time.sleep(0.001)


async def websocket_stream(websocket : WebSocket) -> None:
	stream_mode = get_websocket_stream_mode(websocket.scope)

	if stream_mode == 'image':
		await handle_image_stream(websocket)

	if stream_mode == 'video':
		await handle_video_stream(websocket)


async def post_stream(request : Request) -> Response:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)
	session_context.set_session_id(session_id)

	if session_id:
		sdp_offer = (await request.body()).decode()
		sdp_answer = rtc_store.add_rtc_viewer(session_id, sdp_offer)

		if sdp_answer:
			return Response(sdp_answer, status_code = 201, media_type = 'application/sdp')

	return Response(status_code = 404)
