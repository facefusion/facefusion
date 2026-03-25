import asyncio
import os
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import List

import cv2
import numpy
from starlette.requests import Request
from starlette.responses import Response
from starlette.websockets import WebSocket

from facefusion import logger, session_context, session_manager, state_manager
from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.apis.session_helper import extract_access_token
from facefusion.apis.stream_helper import STREAM_FPS, STREAM_QUALITY, create_vp8_pipe_encoder, feed_whip_frame, process_stream_frame
from facefusion.streamer import process_vision_frame
from facefusion.types import VisionFrame


JPEG_MAGIC : bytes = b'\xff\xd8'


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


def read_ivf_frames(process, frame_list : List[bytes], frame_lock : threading.Lock) -> None:
	pipe_handle = process.stdout.fileno()

	if os.name != 'nt':
		os.set_blocking(pipe_handle, True)

	header = b''

	while len(header) < 32:
		chunk = os.read(pipe_handle, 32 - len(header))

		if not chunk:
			return

		header += chunk

	while True:
		frame_header = b''

		while len(frame_header) < 12:
			chunk = os.read(pipe_handle, 12 - len(frame_header))

			if not chunk:
				return

			frame_header += chunk

		frame_size = int.from_bytes(frame_header[0:4], 'little')
		frame_data = b''

		while len(frame_data) < frame_size:
			chunk = os.read(pipe_handle, frame_size - len(frame_data))

			if not chunk:
				return

			frame_data += chunk

		with frame_lock:
			frame_list.append(frame_data)


def run_rtc_direct_pipeline(latest_frame_holder : list, lock : threading.Lock, stop_event : threading.Event, ready_event : threading.Event, stream_path : str) -> None:
	from facefusion import rtc

	encoder = None
	vp8_frames : List[bytes] = []
	vp8_lock = threading.Lock()
	output_deque : deque = deque()

	with ThreadPoolExecutor(max_workers = state_manager.get_item('execution_thread_count')) as executor:
		futures = []

		while not stop_event.is_set():
			with lock:
				capture_frame = latest_frame_holder[0]
				latest_frame_holder[0] = None

			if capture_frame is not None:
				h, w = capture_frame.shape[:2]

				if w > 640:
					scale = 640 / w
					capture_frame = cv2.resize(capture_frame, (640, int(h * scale) - int(h * scale) % 2))

				if len(futures) < 4:
					future = executor.submit(process_stream_frame, capture_frame)
					futures.append(future)

			for future_done in [ future for future in futures if future.done() ]:
				output_deque.append(future_done.result())
				futures.remove(future_done)

			if encoder and encoder.poll() is not None:
				stderr_output = encoder.stderr.read() if encoder.stderr else b''
				logger.error('vp8 encoder died: ' + stderr_output.decode(), __name__)
				break

			while output_deque:
				temp_vision_frame = output_deque.popleft()

				if not encoder:
					height, width = temp_vision_frame.shape[:2]
					encoder = create_vp8_pipe_encoder(width, height, STREAM_FPS, STREAM_QUALITY)
					threading.Thread(target = read_ivf_frames, args = (encoder, vp8_frames, vp8_lock), daemon = True).start()
					logger.info('vp8 direct encoder started ' + str(width) + 'x' + str(height), __name__)

				feed_whip_frame(encoder, temp_vision_frame)

			with vp8_lock:
				if vp8_frames:
					pending = list(vp8_frames)
					vp8_frames.clear()

					for frame in pending:
						rtc.send_to_viewers(stream_path, frame)

			if not ready_event.is_set() and encoder and encoder.poll() is None:
				time.sleep(0.5)
				ready_event.set()

			if capture_frame is None and not output_deque:
				time.sleep(0.003)

	if encoder:
		encoder.stdin.close()
		encoder.terminate()
		encoder.wait(timeout = 5)


async def websocket_stream_rtc(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	access_token = extract_access_token(websocket.scope)
	session_id = session_manager.find_session_id(access_token)

	session_context.set_session_id(session_id)
	source_paths = state_manager.get_item('source_paths')

	await websocket.accept(subprotocol = subprotocol)

	if source_paths:
		from facefusion import rtc

		stream_path = 'stream/' + session_id
		rtc.create_session(stream_path)
		whep_url = '/' + stream_path + '/whep'

		latest_frame_holder : list = [None]
		whep_sent = False
		lock = threading.Lock()
		stop_event = threading.Event()
		ready_event = threading.Event()
		worker = threading.Thread(target = run_rtc_direct_pipeline, args = (latest_frame_holder, lock, stop_event, ready_event, stream_path), daemon = True)
		worker.start()

		try:
			while True:
				message = await websocket.receive()

				if not whep_sent and ready_event.is_set():
					await websocket.send_text(whep_url)
					whep_sent = True

				if message.get('bytes'):
					data = message.get('bytes')

					if data[:2] == JPEG_MAGIC:
						frame = cv2.imdecode(numpy.frombuffer(data, numpy.uint8), cv2.IMREAD_COLOR)

						if numpy.any(frame):
							with lock:
								latest_frame_holder[0] = frame

					if data[:2] != JPEG_MAGIC:
						rtc.send_audio(stream_path, data)

		except Exception as exception:
			logger.error(str(exception), __name__)

		stop_event.set()
		loop = asyncio.get_running_loop()
		await loop.run_in_executor(None, worker.join, 10)
		rtc.destroy_session(stream_path)
		return

	await websocket.close()


async def post_whep(request : Request) -> Response:
	from facefusion import rtc

	session_id = request.path_params.get('session_id')
	stream_path = 'stream/' + session_id
	body = await request.body()
	sdp_offer = body.decode('utf-8')
	loop = asyncio.get_running_loop()
	answer = await loop.run_in_executor(None, rtc.handle_whep_offer, stream_path, sdp_offer)

	if answer:
		return Response(answer, status_code = 201, media_type = 'application/sdp')
	return Response(status_code = 404)
