import asyncio
import math
import os
import subprocess
from collections import deque
from collections.abc import AsyncIterator
from typing import Optional

import cv2
import numpy
from starlette.websockets import WebSocket, WebSocketState

from facefusion import rtc_store, session_context, session_manager, state_manager
from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.apis.session_helper import extract_access_token
from facefusion.common_helper import is_linux, is_macos
from facefusion.ffmpeg import spawn_stream
from facefusion.streamer import process_vision_frame
from facefusion.types import Resolution, SessionId, VisionFrame


def calculate_bitrate(resolution : Resolution) -> int: # TODO : improve the bitrate calculation
	pixel_total = resolution[0] * resolution[1]
	bitrate_factor = 3500 / math.sqrt(1920 * 1080)
	return max(400, round(math.sqrt(pixel_total) * bitrate_factor))


def calculate_buffer_size(resolution : Resolution) -> int:
	return calculate_bitrate(resolution) * 2


def read_pipe_buffer(pipe_handle : int, size : int) -> Optional[bytes]:
	byte_buffer = bytearray()
	frame_data = os.read(pipe_handle, size - len(byte_buffer))

	while frame_data:
		byte_buffer += frame_data

		if len(byte_buffer) == size:
			return bytes(byte_buffer)

		frame_data = os.read(pipe_handle, size - len(byte_buffer))

	return None


async def receive_vision_frames(websocket : WebSocket) -> AsyncIterator[VisionFrame]:
	websocket_event = await websocket.receive()

	while websocket_event.get('type') == 'websocket.receive':
		frame_buffer = websocket_event.get('bytes') or b''
		vision_frame = cv2.imdecode(numpy.frombuffer(frame_buffer, numpy.uint8), cv2.IMREAD_COLOR)

		if numpy.any(vision_frame):
			yield vision_frame

		websocket_event = await websocket.receive()


def forward_rtc_frames(encoder : subprocess.Popen[bytes], session_id : SessionId) -> None:
	pipe_handle = encoder.stdout.fileno()

	if is_linux() or is_macos():
		os.set_blocking(pipe_handle, True)

	header = read_pipe_buffer(pipe_handle, 32)

	if header:
		frame_header = read_pipe_buffer(pipe_handle, 12)

		while frame_header:
			frame_size = int.from_bytes(frame_header[0:4], 'little')
			frame_data = read_pipe_buffer(pipe_handle, frame_size)

			if frame_data:
				rtc_store.send_rtc_frame(session_id, frame_data)

			frame_header = read_pipe_buffer(pipe_handle, 12)


def submit_encoder_frame(encoder : subprocess.Popen[bytes], vision_frame_deque : deque[VisionFrame]) -> None:
	output_vision_frame = process_vision_frame(vision_frame_deque[-1])
	encoder.stdin.write(cv2.cvtColor(output_vision_frame, cv2.COLOR_BGR2RGB).tobytes())
	encoder.stdin.flush()


def run_encode_loop(encoder : subprocess.Popen[bytes], vision_frame_deque : deque[VisionFrame]) -> None:
	while vision_frame_deque:
		submit_encoder_frame(encoder, vision_frame_deque)

	encoder.stdin.close()
	encoder.wait()


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

			vision_frame_deque.append(vision_frame)
			rtc_store.create_rtc_stream(session_id)

			event_loop = asyncio.get_running_loop()
			await event_loop.run_in_executor(None, submit_encoder_frame, encoder, vision_frame_deque)
			await websocket.send_text('ready')
			encode_task = event_loop.run_in_executor(None, run_encode_loop, encoder, vision_frame_deque)
			rtc_task = event_loop.run_in_executor(None, forward_rtc_frames, encoder, session_id)

			async for vision_frame in vision_frames:
				vision_frame_deque.append(vision_frame)

			vision_frame_deque.clear()
			await asyncio.gather(encode_task, rtc_task)
			rtc_store.destroy_rtc_stream(session_id)

	if websocket.client_state == WebSocketState.CONNECTED:
		await websocket.close()
