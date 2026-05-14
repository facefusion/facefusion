import asyncio
from collections import deque
from collections.abc import AsyncIterator
from typing import Tuple, cast, get_args

import cv2
import numpy
from starlette.websockets import WebSocket, WebSocketState

from facefusion import rtc_store, session_context, session_manager, state_manager
from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.apis.session_helper import extract_access_token
from facefusion.codecs.aom import create_aom_encoder, destroy_aom_encoder, encode_aom_buffer
from facefusion.codecs.opus import create_opus_encoder, destroy_opus_encoder, encode_opus_buffer
from facefusion.codecs.vpx import create_vpx_encoder, destroy_vpx_encoder, encode_vpx_buffer
from facefusion.streamer import process_vision_frame
from facefusion.types import Resolution, SessionId, VideoCodec, VisionFrame


async def receive_stream_frames(websocket : WebSocket) -> AsyncIterator[Tuple[int, bytes]]:
	websocket_event = await websocket.receive()

	while websocket_event.get('type') == 'websocket.receive':
		frame_buffer = websocket_event.get('bytes') or bytes()

		if len(frame_buffer) > 1:
			yield frame_buffer[0], frame_buffer[1:]

		websocket_event = await websocket.receive()


async def receive_vision_frames(websocket : WebSocket) -> AsyncIterator[VisionFrame]:
	websocket_event = await websocket.receive()

	while websocket_event.get('type') == 'websocket.receive':
		frame_buffer = websocket_event.get('bytes') or bytes()
		vision_frame = cv2.imdecode(numpy.frombuffer(frame_buffer, numpy.uint8), cv2.IMREAD_COLOR)

		if numpy.any(vision_frame):
			yield vision_frame

		websocket_event = await websocket.receive()


def run_aom_encode_loop(vision_frame_deque : deque[VisionFrame], session_id : SessionId, initial_resolution : Resolution, keyframe_interval : int) -> None:
	aom_encoder = create_aom_encoder(initial_resolution, 4500, 8, 10)
	current_resolution = initial_resolution
	pts = 0

	while vision_frame_deque:
		vision_frame = vision_frame_deque[-1]
		output_frame = process_vision_frame(vision_frame)
		frame_resolution = (output_frame.shape[1], output_frame.shape[0])

		if frame_resolution[0] != current_resolution[0] or frame_resolution[1] != current_resolution[1]:
			if aom_encoder:
				destroy_aom_encoder(aom_encoder)

			current_resolution = frame_resolution
			aom_encoder = create_aom_encoder(current_resolution, 4500, 8, 10)
			pts = 0

		if aom_encoder:
			yuv_frame = cv2.cvtColor(output_frame, cv2.COLOR_BGR2YUV_I420)
			frame_buffer = encode_aom_buffer(aom_encoder, yuv_frame.tobytes(), frame_resolution, pts)

			if frame_buffer:
				rtc_store.send_rtc_video(session_id, frame_buffer)

		pts += 1

	if aom_encoder:
		destroy_aom_encoder(aom_encoder)


def run_vp8_encode_loop(vision_frame_deque : deque[VisionFrame], session_id : SessionId, initial_resolution : Resolution, keyframe_interval : int) -> None:
	vpx_encoder = create_vpx_encoder(initial_resolution, 4500, 8, 16)
	current_resolution = initial_resolution
	pts = 0

	while vision_frame_deque:
		vision_frame = vision_frame_deque[-1]
		output_frame = process_vision_frame(vision_frame)
		frame_resolution = (output_frame.shape[1], output_frame.shape[0])

		if frame_resolution[0] != current_resolution[0] or frame_resolution[1] != current_resolution[1]:
			if vpx_encoder:
				destroy_vpx_encoder(vpx_encoder)

			current_resolution = frame_resolution
			vpx_encoder = create_vpx_encoder(current_resolution, 4500, 8, 16)
			pts = 0

		if vpx_encoder:
			yuv_frame = cv2.cvtColor(output_frame, cv2.COLOR_BGR2YUV_I420)
			frame_buffer = encode_vpx_buffer(vpx_encoder, yuv_frame.tobytes(), frame_resolution, pts)

			if frame_buffer:
				rtc_store.send_rtc_video(session_id, frame_buffer)

		pts += 1

	if vpx_encoder:
		destroy_vpx_encoder(vpx_encoder)


# TODO: extract shared session setup from handle_image_stream and handle_video_stream, guard session_id like handle_video_stream
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
	stream_codec : VideoCodec = 'av1'

	if websocket.query_params.get('codec') in get_args(VideoCodec):
		stream_codec = cast(VideoCodec, websocket.query_params.get('codec'))

	await websocket.accept(subprotocol = subprotocol)

	if session_id:
		stream_frames = receive_stream_frames(websocket)
		first_vision_frame = None

		# TODO: audio frames may arrive before video due to ScriptProcessor firing faster than canvas toBlob
		async for first_frame_type, first_frame_buffer in stream_frames:
			if first_frame_type == 1:
				first_vision_frame = cv2.imdecode(numpy.frombuffer(first_frame_buffer, numpy.uint8), cv2.IMREAD_COLOR)
				break

		if numpy.any(first_vision_frame):
			resolution : Resolution = (first_vision_frame.shape[1], first_vision_frame.shape[0])
			keyframe_interval = int(state_manager.get_item('output_video_fps') or 30) # TODO: remove hardcoded via stream_video_fps
			vision_frame_deque : deque[VisionFrame] = deque(maxlen = 1)
			opus_encoder = create_opus_encoder(48000, 2) # TODO: guard against opus_encoder being None
			audio_temp = numpy.array([], dtype = numpy.float32)
			audio_timestamp = 0

			vision_frame_deque.append(first_vision_frame)
			rtc_store.create_rtc_stream(session_id)

			event_loop = asyncio.get_running_loop()
			encode_loop = run_aom_encode_loop

			if stream_codec == 'vp8':
				encode_loop = run_vp8_encode_loop

			video_encode_task = event_loop.run_in_executor(None, encode_loop, vision_frame_deque, session_id, resolution, keyframe_interval)
			await websocket.send_text('ready')

			async for frame_type, frame_buffer in stream_frames:
				if frame_type == 1:
					vision_frame = cv2.imdecode(numpy.frombuffer(frame_buffer, numpy.uint8), cv2.IMREAD_COLOR)

					if numpy.any(vision_frame):
						vision_frame_deque.append(vision_frame)

				if frame_type == 2:
					audio_temp = numpy.concatenate([ audio_temp, numpy.frombuffer(frame_buffer, dtype = numpy.float32) ])

					while len(audio_temp) >= 1920:
						audio_chunk = audio_temp[:1920]
						audio_temp = audio_temp[1920:]
						audio_buffer = encode_opus_buffer(opus_encoder, audio_chunk.tobytes(), 960)

						if audio_buffer:
							rtc_store.send_rtc_audio(session_id, audio_buffer, audio_timestamp)

						audio_timestamp += 960

			vision_frame_deque.clear()
			await video_encode_task

			if opus_encoder:
				destroy_opus_encoder(opus_encoder)

			rtc_store.destroy_rtc_stream(session_id)

	if websocket.client_state == WebSocketState.CONNECTED:
		await websocket.close()
