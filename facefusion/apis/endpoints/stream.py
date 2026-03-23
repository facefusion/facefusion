import asyncio
import fcntl
import os as _os
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Deque, List

import cv2
import numpy
from starlette.websockets import WebSocket

from facefusion import logger, session_context, session_manager, state_manager
from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.apis.session_helper import extract_access_token
from facefusion import mediamtx
from facefusion.apis.stream_helper import STREAM_FPS, STREAM_QUALITY, close_fmp4_encoder, close_whip_encoder, collect_fmp4_chunks, create_fmp4_encoder, create_vp8_pipe_encoder, create_whip_encoder, feed_whip_audio, feed_whip_frame, process_stream_frame, read_fmp4_output
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


def run_whip_pipeline(latest_frame_holder : list, lock : threading.Lock, stop_event : threading.Event, ready_event : threading.Event, audio_write_fd_holder : list, stream_path : str) -> None:
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

			if encoder and encoder.poll() is not None:
				stderr_output = encoder.stderr.read() if encoder.stderr else b''
				logger.error('encoder died with code ' + str(encoder.returncode) + ': ' + stderr_output.decode(), __name__)
				break

			while output_deque:
				temp_vision_frame = output_deque.popleft()

				if not encoder:
					height, width = temp_vision_frame.shape[:2]
					whip_url = mediamtx.get_whip_url(stream_path)
					encoder, audio_write_fd = create_whip_encoder(width, height, STREAM_FPS, STREAM_QUALITY, whip_url)
					audio_write_fd_holder[0] = audio_write_fd
					logger.info('whip encoder started ' + str(width) + 'x' + str(height), __name__)

				feed_whip_frame(encoder, temp_vision_frame)

			if encoder and not ready_event.is_set() and mediamtx.is_path_ready(stream_path):
				ready_event.set()

			if capture_frame is None and not output_deque:
				time.sleep(0.005)

	if encoder:
		close_whip_encoder(encoder, audio_write_fd)


async def websocket_stream_whip(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	access_token = extract_access_token(websocket.scope)
	session_id = session_manager.find_session_id(access_token)

	session_context.set_session_id(session_id)
	source_paths = state_manager.get_item('source_paths')

	await websocket.accept(subprotocol = subprotocol)

	if source_paths:
		stream_path = 'stream/' + session_id
		mediamtx.remove_path(stream_path)
		mediamtx.add_path(stream_path)
		logger.info('mediamtx path added ' + stream_path, __name__)

		latest_frame_holder : list = [None]
		audio_write_fd_holder : list = [-1]
		whep_sent = False
		lock = threading.Lock()
		stop_event = threading.Event()
		ready_event = threading.Event()
		worker = threading.Thread(target = run_whip_pipeline, args = (latest_frame_holder, lock, stop_event, ready_event, audio_write_fd_holder, stream_path), daemon = True)
		worker.start()

		try:
			while True:
				message = await websocket.receive()

				if not whep_sent and ready_event.is_set():
					whep_url = mediamtx.get_whep_url(stream_path)
					await websocket.send_text(whep_url)
					whep_sent = True

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
		loop = asyncio.get_running_loop()
		await loop.run_in_executor(None, worker.join, 10)
		mediamtx.remove_path(stream_path)
		return

	await websocket.close()


def run_fmp4_pipeline(latest_frame_holder : list, lock : threading.Lock, stop_event : threading.Event, output_chunks : List[bytes], output_lock : threading.Lock, audio_write_fd_holder : list) -> None:
	encoder = None
	audio_write_fd = -1
	reader_thread = None
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

			if encoder and encoder.poll() is not None:
				stderr_output = encoder.stderr.read() if encoder.stderr else b''
				logger.error('fmp4 encoder died with code ' + str(encoder.returncode) + ': ' + stderr_output.decode(), __name__)
				break

			while output_deque:
				temp_vision_frame = output_deque.popleft()

				if not encoder:
					height, width = temp_vision_frame.shape[:2]
					encoder, audio_write_fd = create_fmp4_encoder(width, height, STREAM_FPS, STREAM_QUALITY)
					audio_write_fd_holder[0] = audio_write_fd
					reader_thread = threading.Thread(target = read_fmp4_output, args = (encoder, output_chunks, output_lock), daemon = True)
					reader_thread.start()
					logger.info('fmp4 encoder started ' + str(width) + 'x' + str(height), __name__)

				feed_whip_frame(encoder, temp_vision_frame)

			if capture_frame is None and not output_deque:
				time.sleep(0.005)

	if encoder:
		close_fmp4_encoder(encoder, audio_write_fd)


async def websocket_stream_live(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	access_token = extract_access_token(websocket.scope)
	session_id = session_manager.find_session_id(access_token)

	session_context.set_session_id(session_id)
	source_paths = state_manager.get_item('source_paths')

	await websocket.accept(subprotocol = subprotocol)

	if source_paths:
		latest_frame_holder : list = [None]
		audio_write_fd_holder : list = [-1]
		output_chunks : List[bytes] = []
		lock = threading.Lock()
		output_lock = threading.Lock()
		stop_event = threading.Event()
		worker = threading.Thread(target = run_fmp4_pipeline, args = (latest_frame_holder, lock, stop_event, output_chunks, output_lock, audio_write_fd_holder), daemon = True)
		worker.start()

		try:
			while True:
				message = await websocket.receive()

				chunks = collect_fmp4_chunks(output_chunks, output_lock)

				if chunks:
					await websocket.send_bytes(chunks)

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
		loop = asyncio.get_running_loop()
		await loop.run_in_executor(None, worker.join, 10)
		return

	await websocket.close()


def run_mjpeg_pipeline(latest_frame_holder : list, lock : threading.Lock, stop_event : threading.Event, output_holder : list, output_lock : threading.Lock) -> None:
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
				is_success, encoded = cv2.imencode('.jpg', temp_vision_frame, [cv2.IMWRITE_JPEG_QUALITY, 92])

				if is_success:
					with output_lock:
						output_holder[0] = encoded.tobytes()

			if capture_frame is None and not output_deque:
				time.sleep(0.005)


async def websocket_stream_mjpeg(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	access_token = extract_access_token(websocket.scope)
	session_id = session_manager.find_session_id(access_token)

	session_context.set_session_id(session_id)
	source_paths = state_manager.get_item('source_paths')

	await websocket.accept(subprotocol = subprotocol)

	if source_paths:
		latest_frame_holder : list = [None]
		output_holder : list = [None]
		lock = threading.Lock()
		output_lock = threading.Lock()
		stop_event = threading.Event()
		worker = threading.Thread(target = run_mjpeg_pipeline, args = (latest_frame_holder, lock, stop_event, output_holder, output_lock), daemon = True)
		worker.start()

		try:
			while True:
				message = await websocket.receive()

				with output_lock:
					jpeg_data = output_holder[0]
					output_holder[0] = None

				if jpeg_data:
					await websocket.send_bytes(jpeg_data)

				if message.get('bytes'):
					data = message.get('bytes')

					if data[:2] == JPEG_MAGIC:
						frame = cv2.imdecode(numpy.frombuffer(data, numpy.uint8), cv2.IMREAD_COLOR)

						if numpy.any(frame):
							with lock:
								latest_frame_holder[0] = frame

		except Exception as exception:
			logger.error(str(exception), __name__)

		stop_event.set()
		loop = asyncio.get_running_loop()
		await loop.run_in_executor(None, worker.join, 10)
		return

	await websocket.close()


async def websocket_stream_audio(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	access_token = extract_access_token(websocket.scope)
	session_id = session_manager.find_session_id(access_token)

	session_context.set_session_id(session_id)

	await websocket.accept(subprotocol = subprotocol)

	try:
		while True:
			message = await websocket.receive()

			if message.get('bytes'):
				await websocket.send_bytes(message.get('bytes'))
	except Exception:
		pass


async def websocket_stream_whip_py(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	access_token = extract_access_token(websocket.scope)
	session_id = session_manager.find_session_id(access_token)

	session_context.set_session_id(session_id)
	source_paths = state_manager.get_item('source_paths')

	await websocket.accept(subprotocol = subprotocol)

	if source_paths:
		from facefusion.aiortc_bridge import AiortcBridge

		bridge = AiortcBridge()
		await bridge.start()
		whep_url = 'http://localhost:' + str(bridge.port) + '/whep'

		latest_frame_holder : list = [None]
		whep_sent = False
		lock = threading.Lock()
		stop_event = threading.Event()
		ready_event = threading.Event()
		worker = threading.Thread(target = run_aiortc_pipeline, args = (latest_frame_holder, lock, stop_event, ready_event, bridge), daemon = True)
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
						bridge.push_audio(data)

		except Exception as exception:
			logger.error(str(exception), __name__)

		stop_event.set()
		loop = asyncio.get_running_loop()
		await loop.run_in_executor(None, worker.join, 10)
		await bridge.stop()
		return

	await websocket.close()


def run_aiortc_pipeline(latest_frame_holder : list, lock : threading.Lock, stop_event : threading.Event, ready_event : threading.Event, bridge : object) -> None:
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
				bridge.push_frame(temp_vision_frame)

			if not ready_event.is_set():
				time.sleep(2)
				ready_event.set()

			if capture_frame is None and not output_deque:
				time.sleep(0.005)


def read_h264_output(process, h264_chunks : List[bytes], h264_lock : threading.Lock) -> None:
	fd = process.stdout.fileno()
	flags = fcntl.fcntl(fd, fcntl.F_GETFL)
	fcntl.fcntl(fd, fcntl.F_SETFL, flags & ~_os.O_NONBLOCK)

	while True:
		chunk = _os.read(fd, 4096)

		if not chunk:
			break

		with h264_lock:
			h264_chunks.append(chunk)


def read_ivf_frames(process, frame_list : List[bytes], frame_lock : threading.Lock) -> None:
	fd = process.stdout.fileno()
	flags = fcntl.fcntl(fd, fcntl.F_GETFL)
	fcntl.fcntl(fd, fcntl.F_SETFL, flags & ~_os.O_NONBLOCK)

	header = b''

	while len(header) < 32:
		chunk = _os.read(fd, 32 - len(header))

		if not chunk:
			return

		header += chunk

	while True:
		frame_header = b''

		while len(frame_header) < 12:
			chunk = _os.read(fd, 12 - len(frame_header))

			if not chunk:
				return

			frame_header += chunk

		frame_size = int.from_bytes(frame_header[0:4], 'little')
		frame_data = b''

		while len(frame_data) < frame_size:
			chunk = _os.read(fd, frame_size - len(frame_data))

			if not chunk:
				return

			frame_data += chunk

		with frame_lock:
			frame_list.append(frame_data)


def run_h264_dc_pipeline(latest_frame_holder : list, lock : threading.Lock, stop_event : threading.Event, ready_event : threading.Event, backend : str, stream_path : str, rtp_port : int) -> None:
	encoder = None
	reader_thread = None
	vp8_frames : List[bytes] = []
	vp8_lock = threading.Lock()
	output_deque : Deque[VisionFrame] = deque()
	udp_sock = None

	if backend == 'relay':
		import socket as sock
		udp_sock = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)

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

			if encoder and encoder.poll() is not None:
				stderr_output = encoder.stderr.read() if encoder.stderr else b''
				logger.error('vp8 encoder died: ' + stderr_output.decode(), __name__)
				break

			while output_deque:
				temp_vision_frame = output_deque.popleft()

				if not encoder:
					height, width = temp_vision_frame.shape[:2]
					encoder = create_vp8_pipe_encoder(width, height, STREAM_FPS, STREAM_QUALITY)
					reader_thread = threading.Thread(target = read_ivf_frames, args = (encoder, vp8_frames, vp8_lock), daemon = True)
					reader_thread.start()
					logger.info('vp8 encoder started ' + str(width) + 'x' + str(height) + ' [' + backend + ']', __name__)

				feed_whip_frame(encoder, temp_vision_frame)

			with vp8_lock:
				if vp8_frames:
					pending = list(vp8_frames)
					vp8_frames.clear()

					for frame in pending:
						if backend == 'relay' and udp_sock:
							if len(frame) <= 65000:
								udp_sock.sendto(frame, ('127.0.0.1', rtp_port))
						if backend == 'rtc':
							from facefusion import rtc
							rtc.send_vp8_frame(stream_path, frame)

			if not ready_event.is_set() and encoder and encoder.poll() is None:
				time.sleep(1)
				ready_event.set()

			if capture_frame is None and not output_deque:
				time.sleep(0.005)

	if encoder:
		encoder.stdin.close()
		encoder.terminate()
		encoder.wait(timeout = 5)

	if udp_sock:
		udp_sock.close()


async def websocket_stream_whip_dc(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	access_token = extract_access_token(websocket.scope)
	session_id = session_manager.find_session_id(access_token)

	session_context.set_session_id(session_id)
	source_paths = state_manager.get_item('source_paths')

	await websocket.accept(subprotocol = subprotocol)

	if source_paths:
		from facefusion import whip_relay
		stream_path = 'stream/' + session_id
		rtp_port = whip_relay.create_session(stream_path)

		if not rtp_port:
			logger.error('failed to create relay session', __name__)
			await websocket.close()
			return

		latest_frame_holder : list = [None]
		whep_sent = False
		lock = threading.Lock()
		stop_event = threading.Event()
		ready_event = threading.Event()
		worker = threading.Thread(target = run_h264_dc_pipeline, args = (latest_frame_holder, lock, stop_event, ready_event, 'relay', stream_path, rtp_port), daemon = True)
		worker.start()

		try:
			while True:
				message = await websocket.receive()

				if not whep_sent and ready_event.is_set():
					whep_url = whip_relay.get_whep_url(stream_path)
					await websocket.send_text(whep_url)
					whep_sent = True

				if message.get('bytes'):
					data = message.get('bytes')

					if data[:2] == JPEG_MAGIC:
						frame = cv2.imdecode(numpy.frombuffer(data, numpy.uint8), cv2.IMREAD_COLOR)

						if numpy.any(frame):
							with lock:
								latest_frame_holder[0] = frame

		except Exception as exception:
			logger.error(str(exception), __name__)

		stop_event.set()
		loop = asyncio.get_running_loop()
		await loop.run_in_executor(None, worker.join, 10)
		return

	await websocket.close()


async def websocket_stream_whip_aio(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	access_token = extract_access_token(websocket.scope)
	session_id = session_manager.find_session_id(access_token)

	session_context.set_session_id(session_id)
	source_paths = state_manager.get_item('source_paths')

	await websocket.accept(subprotocol = subprotocol)

	if source_paths:
		from facefusion.aiortc_bridge import AiortcBridge

		bridge = AiortcBridge()
		await bridge.start()
		whep_url = 'http://localhost:' + str(bridge.port) + '/whep'

		latest_frame_holder : list = [None]
		whep_sent = False
		lock = threading.Lock()
		stop_event = threading.Event()
		ready_event = threading.Event()
		worker = threading.Thread(target = run_aiortc_pipeline, args = (latest_frame_holder, lock, stop_event, ready_event, bridge), daemon = True)
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
						bridge.push_audio(data)

		except Exception as exception:
			logger.error(str(exception), __name__)

		stop_event.set()
		loop = asyncio.get_running_loop()
		await loop.run_in_executor(None, worker.join, 10)
		await bridge.stop()
		return

	await websocket.close()


def run_rtc_direct_pipeline(latest_frame_holder : list, lock : threading.Lock, stop_event : threading.Event, ready_event : threading.Event, stream_path : str) -> None:
	from facefusion import rtc
	encoder = None
	reader_thread = None
	vp8_frames : List[bytes] = []
	vp8_lock = threading.Lock()
	output_deque : Deque[VisionFrame] = deque()

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
					reader_thread = threading.Thread(target = read_ivf_frames, args = (encoder, vp8_frames, vp8_lock), daemon = True)
					reader_thread.start()
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
		whep_url = 'http://localhost:' + str(rtc.WHEP_PORT) + '/' + stream_path + '/whep'

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

		except Exception as exception:
			logger.error(str(exception), __name__)

		stop_event.set()
		loop = asyncio.get_running_loop()
		await loop.run_in_executor(None, worker.join, 10)
		rtc.destroy_session(stream_path)
		return

	await websocket.close()
