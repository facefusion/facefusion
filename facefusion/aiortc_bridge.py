import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

import numpy
from aiortc import RTCPeerConnection, RTCSessionDescription, AudioStreamTrack, VideoStreamTrack
from av import AudioFrame, VideoFrame

from facefusion import logger
from facefusion.types import VisionFrame

BRIDGE_PORT_START : int = 8893
AUDIO_SAMPLE_RATE : int = 48000


class FramePushTrack(VideoStreamTrack):
	kind = 'video'

	def __init__(self) -> None:
		super().__init__()
		self._frame : Optional[VisionFrame] = None
		self._lock = threading.Lock()
		self._started = False

	def push(self, vision_frame : VisionFrame) -> None:
		with self._lock:
			self._frame = vision_frame

	async def recv(self) -> VideoFrame:
		pts, time_base = await self.next_timestamp()

		with self._lock:
			frame_data = self._frame

		if frame_data is None:
			frame_data = numpy.zeros((240, 320, 3), dtype = numpy.uint8)

		if not self._started:
			self._started = True
			logger.info('aiortc track sending first frame', __name__)

		video_frame = VideoFrame.from_ndarray(frame_data, format = 'bgr24')
		video_frame.pts = pts
		video_frame.time_base = time_base
		return video_frame


class AudioPushTrack(AudioStreamTrack):
	kind = 'audio'

	def __init__(self) -> None:
		super().__init__()
		self._buffer = bytearray()
		self._lock = threading.Lock()
		self._pts = 0
		self._frame_samples = 960

	def push(self, pcm_data : bytes) -> None:
		with self._lock:
			self._buffer.extend(pcm_data)

			if len(self._buffer) > AUDIO_SAMPLE_RATE * 4:
				self._buffer = self._buffer[-AUDIO_SAMPLE_RATE * 4:]

	async def recv(self) -> AudioFrame:
		await asyncio.sleep(self._frame_samples / AUDIO_SAMPLE_RATE)
		needed = self._frame_samples * 2 * 2

		with self._lock:
			if len(self._buffer) >= needed:
				chunk = bytes(self._buffer[:needed])
				del self._buffer[:needed]
			else:
				chunk = None

		if chunk:
			pcm = numpy.frombuffer(chunk, dtype = numpy.int16).reshape(1, -1)
		else:
			pcm = numpy.zeros((1, self._frame_samples * 2), dtype = numpy.int16)

		audio_frame = AudioFrame.from_ndarray(pcm, format = 's16', layout = 'stereo')
		audio_frame.sample_rate = AUDIO_SAMPLE_RATE
		audio_frame.pts = self._pts
		self._pts += self._frame_samples
		return audio_frame


class AiortcBridge:
	def __init__(self) -> None:
		global BRIDGE_PORT_START
		self.port = BRIDGE_PORT_START
		BRIDGE_PORT_START += 1
		self.video_track = FramePushTrack()
		self.audio_track = AudioPushTrack()
		self.pcs : list = []
		self._http_thread : Optional[threading.Thread] = None
		self._running = False
		self._has_viewer = False
		self._loop = None

	async def start(self) -> None:
		self._running = True
		self._loop = asyncio.get_event_loop()
		self._http_thread = threading.Thread(target = self._run_http, daemon = True)
		self._http_thread.start()
		logger.info('aiortc bridge started on port ' + str(self.port), __name__)

	async def stop(self) -> None:
		self._running = False

		for pc in self.pcs:
			try:
				loop = asyncio.get_event_loop()
				asyncio.run_coroutine_threadsafe(pc.close(), loop)
			except Exception:
				pass

	def push_frame(self, vision_frame : VisionFrame) -> None:
		self.video_track.push(vision_frame)

	def push_audio(self, audio_data : bytes) -> None:
		self.audio_track.push(audio_data)

	def has_viewer(self) -> bool:
		return self._has_viewer

	def _handle_whep(self, sdp_offer : str) -> Optional[str]:
		if not self._loop:
			return None

		future = asyncio.run_coroutine_threadsafe(self._create_pc(sdp_offer), self._loop)

		try:
			return future.result(timeout = 10)
		except Exception as exception:
			logger.error('whep error: ' + str(exception), __name__)
			return None

	async def _create_pc(self, sdp_offer : str) -> Optional[str]:
		pc = RTCPeerConnection()
		self.pcs.append(pc)
		pc.addTrack(self.video_track)
		pc.addTrack(self.audio_track)

		offer = RTCSessionDescription(sdp = sdp_offer, type = 'offer')
		await pc.setRemoteDescription(offer)
		answer = await pc.createAnswer()
		await pc.setLocalDescription(answer)
		self._has_viewer = True
		return pc.localDescription.sdp

	def _run_http(self) -> None:
		bridge = self

		class WhepHandler(BaseHTTPRequestHandler):
			def log_message(self, format, *args) -> None:
				pass

			def do_OPTIONS(self) -> None:
				self.send_response(200)
				self.send_header('Access-Control-Allow-Origin', '*')
				self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
				self.send_header('Access-Control-Allow-Headers', 'Content-Type')
				self.end_headers()

			def do_POST(self) -> None:
				content_length = int(self.headers.get('Content-Length', 0))
				body = self.rfile.read(content_length).decode('utf-8') if content_length else ''
				answer = bridge._handle_whep(body)

				if answer:
					self.send_response(201)
					self.send_header('Content-Type', 'application/sdp')
					self.send_header('Access-Control-Allow-Origin', '*')
					self.end_headers()
					self.wfile.write(answer.encode('utf-8'))
				else:
					self.send_response(500)
					self.send_header('Access-Control-Allow-Origin', '*')
					self.end_headers()

		server = HTTPServer(('0.0.0.0', self.port), WhepHandler)
		server.timeout = 1

		while self._running:
			server.handle_request()


class WhipAiortcBridge:
	def __init__(self) -> None:
		global BRIDGE_PORT_START
		self.port = BRIDGE_PORT_START
		BRIDGE_PORT_START += 1
		self.whip_port = BRIDGE_PORT_START
		BRIDGE_PORT_START += 1
		self._ingest_pc = None
		self._relay_track = None
		self._viewer_pcs : list = []
		self._http_thread : Optional[threading.Thread] = None
		self._running = False
		self._loop = None
		self._ingest_ready = False

	async def start(self) -> None:
		self._running = True
		self._loop = asyncio.get_event_loop()
		self._http_thread = threading.Thread(target = self._run_http, daemon = True)
		self._http_thread.start()
		logger.info('whip-aiortc bridge whip=' + str(self.whip_port) + ' whep=' + str(self.port), __name__)

	async def stop(self) -> None:
		self._running = False

		if self._ingest_pc:
			await self._ingest_pc.close()

		for pc in self._viewer_pcs:
			await pc.close()

	def get_whip_url(self) -> str:
		return 'http://localhost:' + str(self.whip_port) + '/whip'

	def get_whep_url(self) -> str:
		return 'http://localhost:' + str(self.port) + '/whep'

	def is_ready(self) -> bool:
		return self._ingest_ready

	def _handle_whip(self, sdp_offer : str) -> Optional[str]:
		if not self._loop:
			return None

		future = asyncio.run_coroutine_threadsafe(self._create_ingest(sdp_offer), self._loop)

		try:
			return future.result(timeout = 10)
		except Exception as exception:
			logger.error('whip ingest error: ' + str(exception), __name__)
			return None

	def _handle_whep(self, sdp_offer : str) -> Optional[str]:
		if not self._loop:
			return None

		future = asyncio.run_coroutine_threadsafe(self._create_viewer(sdp_offer), self._loop)

		try:
			return future.result(timeout = 10)
		except Exception as exception:
			logger.error('whep error: ' + str(exception), __name__)
			return None

	async def _create_ingest(self, sdp_offer : str) -> Optional[str]:
		from aiortc import MediaStreamTrack
		from aiortc.contrib.media import MediaRelay

		pc = RTCPeerConnection()
		self._ingest_pc = pc
		self._relay = MediaRelay()

		@pc.on('track')
		def on_track(track : MediaStreamTrack) -> None:
			if track.kind == 'video':
				self._relay_track = self._relay.subscribe(track)
				self._ingest_ready = True
				logger.info('whip ingest video track received', __name__)

		offer = RTCSessionDescription(sdp = sdp_offer, type = 'offer')
		await pc.setRemoteDescription(offer)
		answer = await pc.createAnswer()
		await pc.setLocalDescription(answer)
		return pc.localDescription.sdp

	async def _create_viewer(self, sdp_offer : str) -> Optional[str]:
		pc = RTCPeerConnection()
		self._viewer_pcs.append(pc)

		if self._relay_track:
			pc.addTrack(self._relay_track)

		offer = RTCSessionDescription(sdp = sdp_offer, type = 'offer')
		await pc.setRemoteDescription(offer)
		answer = await pc.createAnswer()
		await pc.setLocalDescription(answer)
		return pc.localDescription.sdp

	def _run_http(self) -> None:
		bridge = self

		class Handler(BaseHTTPRequestHandler):
			def log_message(self, format, *args) -> None:
				pass

			def do_OPTIONS(self) -> None:
				self.send_response(200)
				self.send_header('Access-Control-Allow-Origin', '*')
				self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS, DELETE')
				self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
				self.end_headers()

			def do_POST(self) -> None:
				content_length = int(self.headers.get('Content-Length', 0))
				body = self.rfile.read(content_length).decode('utf-8') if content_length else ''
				path = self.path

				if '/whip' in path:
					answer = bridge._handle_whip(body)
				elif '/whep' in path:
					answer = bridge._handle_whep(body)
				else:
					self.send_response(404)
					self.end_headers()
					return

				if answer:
					self.send_response(201)
					self.send_header('Content-Type', 'application/sdp')
					self.send_header('Location', path)
					self.send_header('Access-Control-Allow-Origin', '*')
					self.send_header('Access-Control-Expose-Headers', 'Location')
					self.end_headers()
					self.wfile.write(answer.encode('utf-8'))
				else:
					self.send_response(500)
					self.send_header('Access-Control-Allow-Origin', '*')
					self.end_headers()

		whip_server = HTTPServer(('0.0.0.0', self.whip_port), Handler)
		whip_server.timeout = 0.5
		whep_server = HTTPServer(('0.0.0.0', self.port), Handler)
		whep_server.timeout = 0.5

		while self._running:
			whip_server.handle_request()
			whep_server.handle_request()
