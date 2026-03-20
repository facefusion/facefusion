import asyncio
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Deque

import cv2
import numpy
from starlette.websockets import WebSocket

from facefusion import logger, session_context, session_manager, state_manager
from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.apis.session_helper import extract_access_token
from facefusion import mediamtx
from facefusion.apis.stream_helper import STREAM_FPS, STREAM_QUALITY, close_whip_encoder, create_whip_encoder, feed_whip_audio, feed_whip_frame, process_stream_frame
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


def run_whip_pipeline(latest_frame_holder : list, lock : threading.Lock, stop_event : threading.Event, audio_write_fd_holder : list) -> None:
	encoder = None
	audio_write_fd = -1
	output_deque : Deque[VisionFrame] = deque()

	with ThreadPoolExecutor(max_workers = state_manager.get_item('execution_thread_count')) as executor:
		futures = []

		while not stop_event.is_set():
			with lock:
				capture_frame = latest_frame_holder[0]
				latest_frame_holder[0] = None

			if capture_frame is not None:
				future = executor.submit(process_stream_frame, capture_frame)
				futures.append(future)

			for future_done in [ future for future in futures if future.done() ]:
				output_deque.append(future_done.result())
				futures.remove(future_done)

			while output_deque:
				temp_vision_frame = output_deque.popleft()

				if not encoder:
					height, width = temp_vision_frame.shape[:2]
					encoder, audio_write_fd = create_whip_encoder(width, height, STREAM_FPS, STREAM_QUALITY)
					audio_write_fd_holder[0] = audio_write_fd
					logger.info('whip encoder started ' + str(width) + 'x' + str(height), __name__)

				feed_whip_frame(encoder, temp_vision_frame)

			if capture_frame is None and not output_deque:
				time.sleep(0.005)

	if encoder:
		stderr_output = encoder.stderr.read() if encoder.stderr else b''

		if stderr_output:
			logger.error('ffmpeg: ' + stderr_output.decode(), __name__)

		close_whip_encoder(encoder, audio_write_fd)


async def websocket_stream_whip(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	access_token = extract_access_token(websocket.scope)
	session_id = session_manager.find_session_id(access_token)

	session_context.set_session_id(session_id)
	source_paths = state_manager.get_item('source_paths')

	await websocket.accept(subprotocol = subprotocol)

	if source_paths:
		mediamtx_process = mediamtx.start()
		is_ready = await asyncio.get_running_loop().run_in_executor(None, mediamtx.wait_for_ready)

		if not is_ready:
			logger.error('mediamtx failed to start', __name__)
			mediamtx.stop(mediamtx_process)
			await websocket.close()
			return

		logger.info('mediamtx ready', __name__)

		latest_frame_holder : list = [None]
		audio_write_fd_holder : list = [-1]
		lock = threading.Lock()
		stop_event = threading.Event()
		worker = threading.Thread(target = run_whip_pipeline, args = (latest_frame_holder, lock, stop_event, audio_write_fd_holder), daemon = True)
		worker.start()

		try:
			while True:
				message = await websocket.receive()

				if message.get('bytes'):
					data = message.get('bytes')

					if data[:2] == JPEG_MAGIC:
						frame = cv2.imdecode(numpy.frombuffer(data, numpy.uint8), cv2.IMREAD_COLOR)

						if numpy.any(frame):
							with lock:
								latest_frame_holder[0] = frame

					if data[:2] != JPEG_MAGIC and audio_write_fd_holder[0] > 0:
						feed_whip_audio(audio_write_fd_holder[0], data)

		except Exception as exception:
			logger.error(str(exception), __name__)

		stop_event.set()
		worker.join(timeout = 10)

		if mediamtx_process:
			mediamtx.stop(mediamtx_process)
		return

	await websocket.close()
