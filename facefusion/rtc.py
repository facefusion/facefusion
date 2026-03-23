import ctypes
import ctypes.util
import os
import threading
import time as _time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List, Optional, TypeAlias

from facefusion import logger

RtcLib : TypeAlias = ctypes.CDLL
WHEP_PORT : int = 8892

lib : Optional[RtcLib] = None
sessions : Dict[str, dict] = {}
http_thread : Optional[threading.Thread] = None
running : bool = False

RTC_NEW = 0
RTC_CONNECTING = 1
RTC_CONNECTED = 2
RTC_DISCONNECTED = 3
RTC_FAILED = 4
RTC_CLOSED = 5

RTC_GATHERING_NEW = 0
RTC_GATHERING_INPROGRESS = 1
RTC_GATHERING_COMPLETE = 2

RTC_DIRECTION_SENDONLY = 0
RTC_DIRECTION_RECVONLY = 1
RTC_DIRECTION_SENDRECV = 2
RTC_DIRECTION_INACTIVE = 3
RTC_DIRECTION_UNKNOWN = 4

LOG_CALLBACK_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p)
DESCRIPTION_CALLBACK_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p)
CANDIDATE_CALLBACK_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p)
STATE_CALLBACK_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)
GATHERING_CALLBACK_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)
TRACK_CALLBACK_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)
MESSAGE_CALLBACK_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)


class RtcConfiguration(ctypes.Structure):
	_fields_ =\
	[
		('iceServers', ctypes.POINTER(ctypes.c_char_p)),
		('iceServersCount', ctypes.c_int),
		('proxyServer', ctypes.c_char_p),
		('bindAddress', ctypes.c_char_p),
		('certificateType', ctypes.c_int),
		('iceTransportPolicy', ctypes.c_int),
		('enableIceTcp', ctypes.c_bool),
		('enableIceUdpMux', ctypes.c_bool),
		('disableAutoNegotiation', ctypes.c_bool),
		('forceMediaTransport', ctypes.c_bool),
		('portRangeBegin', ctypes.c_ushort),
		('portRangeEnd', ctypes.c_ushort),
		('mtu', ctypes.c_int),
		('maxMessageSize', ctypes.c_int)
	]


class RtcPacketizerInit(ctypes.Structure):
	_fields_ =\
	[
		('ssrc', ctypes.c_uint32),
		('cname', ctypes.c_char_p),
		('payloadType', ctypes.c_uint8),
		('clockRate', ctypes.c_uint32),
		('sequenceNumber', ctypes.c_uint16),
		('timestamp', ctypes.c_uint32),
		('maxFragmentSize', ctypes.c_uint16),
		('nalSeparator', ctypes.c_int),
		('obuPacketization', ctypes.c_int),
		('playoutDelayId', ctypes.c_uint8),
		('playoutDelayMin', ctypes.c_uint16),
		('playoutDelayMax', ctypes.c_uint16),
		('colorSpaceId', ctypes.c_uint8),
		('colorChromaSitingHorz', ctypes.c_uint8),
		('colorChromaSitingVert', ctypes.c_uint8),
		('colorRange', ctypes.c_uint8),
		('colorPrimaries', ctypes.c_uint8),
		('colorTransfer', ctypes.c_uint8),
		('colorMatrix', ctypes.c_uint8)
	]


def find_library() -> Optional[str]:
	lib_path = ctypes.util.find_library('datachannel')

	if lib_path:
		return lib_path

	search_paths =\
	[
		'/home/henry/local/lib/libdatachannel.so',
		'/usr/local/lib/libdatachannel.so',
		'/usr/lib/libdatachannel.so',
		'/usr/lib/x86_64-linux-gnu/libdatachannel.so'
	]

	for path in search_paths:
		if os.path.isfile(path):
			return path

	return None


def load_library() -> bool:
	global lib

	lib_path = find_library()

	if not lib_path:
		logger.warn('libdatachannel.so not found', __name__)
		return False

	lib = ctypes.CDLL(lib_path)
	setup_prototypes()
	lib.rtcInitLogger(4, LOG_CALLBACK_TYPE(0))
	logger.info('libdatachannel loaded from ' + lib_path, __name__)
	return True


def setup_prototypes() -> None:
	lib.rtcInitLogger.argtypes = [ctypes.c_int, LOG_CALLBACK_TYPE]
	lib.rtcInitLogger.restype = None

	lib.rtcCreatePeerConnection.argtypes = [ctypes.POINTER(RtcConfiguration)]
	lib.rtcCreatePeerConnection.restype = ctypes.c_int

	lib.rtcDeletePeerConnection.argtypes = [ctypes.c_int]
	lib.rtcDeletePeerConnection.restype = ctypes.c_int

	lib.rtcSetLocalDescription.argtypes = [ctypes.c_int, ctypes.c_char_p]
	lib.rtcSetLocalDescription.restype = ctypes.c_int

	lib.rtcSetRemoteDescription.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p]
	lib.rtcSetRemoteDescription.restype = ctypes.c_int

	lib.rtcGetLocalDescription.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
	lib.rtcGetLocalDescription.restype = ctypes.c_int

	lib.rtcAddTrack.argtypes = [ctypes.c_int, ctypes.c_char_p]
	lib.rtcAddTrack.restype = ctypes.c_int

	lib.rtcSetUserPointer.argtypes = [ctypes.c_int, ctypes.c_void_p]
	lib.rtcSetUserPointer.restype = None

	lib.rtcSetLocalDescriptionCallback.argtypes = [ctypes.c_int, DESCRIPTION_CALLBACK_TYPE]
	lib.rtcSetLocalDescriptionCallback.restype = ctypes.c_int

	lib.rtcSetLocalCandidateCallback.argtypes = [ctypes.c_int, CANDIDATE_CALLBACK_TYPE]
	lib.rtcSetLocalCandidateCallback.restype = ctypes.c_int

	lib.rtcSetStateChangeCallback.argtypes = [ctypes.c_int, STATE_CALLBACK_TYPE]
	lib.rtcSetStateChangeCallback.restype = ctypes.c_int

	lib.rtcSetGatheringStateChangeCallback.argtypes = [ctypes.c_int, GATHERING_CALLBACK_TYPE]
	lib.rtcSetGatheringStateChangeCallback.restype = ctypes.c_int

	lib.rtcSetTrackCallback.argtypes = [ctypes.c_int, TRACK_CALLBACK_TYPE]
	lib.rtcSetTrackCallback.restype = ctypes.c_int

	lib.rtcSetMessageCallback.argtypes = [ctypes.c_int, MESSAGE_CALLBACK_TYPE]
	lib.rtcSetMessageCallback.restype = ctypes.c_int

	lib.rtcSendMessage.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
	lib.rtcSendMessage.restype = ctypes.c_int

	lib.rtcSetH264Packetizer.argtypes = [ctypes.c_int, ctypes.POINTER(RtcPacketizerInit)]
	lib.rtcSetH264Packetizer.restype = ctypes.c_int

	lib.rtcSetVP8Packetizer.argtypes = [ctypes.c_int, ctypes.POINTER(RtcPacketizerInit)]
	lib.rtcSetVP8Packetizer.restype = ctypes.c_int

	lib.rtcChainRtcpSrReporter.argtypes = [ctypes.c_int]
	lib.rtcChainRtcpSrReporter.restype = ctypes.c_int

	lib.rtcChainRtcpNackResponder.argtypes = [ctypes.c_int, ctypes.c_uint]
	lib.rtcChainRtcpNackResponder.restype = ctypes.c_int

	lib.rtcSetTrackRtpTimestamp.argtypes = [ctypes.c_int, ctypes.c_uint32]
	lib.rtcSetTrackRtpTimestamp.restype = ctypes.c_int

	lib.rtcSetOpenCallback.argtypes = [ctypes.c_int, ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_void_p)]
	lib.rtcSetOpenCallback.restype = ctypes.c_int

	lib.rtcIsOpen.argtypes = [ctypes.c_int]
	lib.rtcIsOpen.restype = ctypes.c_bool

	lib.rtcSetOpusPacketizer.argtypes = [ctypes.c_int, ctypes.POINTER(RtcPacketizerInit)]
	lib.rtcSetOpusPacketizer.restype = ctypes.c_int


callback_refs : List = []


def create_peer_connection() -> int:
	config = RtcConfiguration()
	config.iceServers = None
	config.iceServersCount = 0
	config.proxyServer = None
	config.bindAddress = None
	config.certificateType = 0
	config.iceTransportPolicy = 0
	config.enableIceTcp = False
	config.enableIceUdpMux = True
	config.disableAutoNegotiation = False
	config.forceMediaTransport = True
	config.portRangeBegin = 0
	config.portRangeEnd = 0
	config.mtu = 0
	config.maxMessageSize = 0
	return lib.rtcCreatePeerConnection(ctypes.byref(config))


next_rtp_port : int = 16000


def create_session(stream_path : str) -> None:
	sessions[stream_path] = {'viewers': [], 'tracks': [], 'rtp_port': 0, 'rtp_fd': None}


def create_rtp_session(stream_path : str) -> int:
	global next_rtp_port
	import socket as sock

	rtp_port = next_rtp_port
	next_rtp_port += 1

	rtp_fd = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
	rtp_fd.bind(('127.0.0.1', rtp_port))
	rtp_fd.settimeout(1.0)

	sessions[stream_path] = {'viewers': [], 'tracks': [], 'rtp_port': rtp_port, 'rtp_fd': rtp_fd}

	rtp_thread = threading.Thread(target = run_rtp_forwarder, args = (stream_path,), daemon = True)
	rtp_thread.start()

	return rtp_port


def run_rtp_forwarder(stream_path : str) -> None:
	session = sessions.get(stream_path)

	if not session:
		return

	rtp_fd = session.get('rtp_fd')

	while running and session.get('rtp_fd'):
		try:
			data, addr = rtp_fd.recvfrom(262144)

			if len(data) < 2:
				continue

			tag = data[0]
			payload = data[1:]

			if tag == 0x01:
				send_to_viewers(stream_path, payload)
			if tag == 0x02:
				send_audio_to_viewers(stream_path, payload)
		except Exception:
			continue


def send_audio_to_viewers(stream_path : str, opus_data : bytes) -> None:
	global audio_pts

	session = sessions.get(stream_path)

	if not session:
		return

	viewers = session.get('viewers')

	if not viewers:
		return

	buf = ctypes.create_string_buffer(opus_data)

	for viewer in viewers:
		if not viewer.get('connected'):
			continue

		audio_track_id = viewer.get('audio_track')

		if not audio_track_id:
			continue

		if not lib.rtcIsOpen(audio_track_id):
			continue

		lib.rtcSetTrackRtpTimestamp(audio_track_id, audio_pts & 0xFFFFFFFF)
		lib.rtcSendMessage(audio_track_id, buf, len(opus_data))

	audio_pts += OPUS_FRAME_SAMPLES


send_start_time : float = 0
audio_pts : int = 0
opus_enc = None
audio_buffer : bytearray = bytearray()
audio_lock : threading.Lock = threading.Lock()
OPUS_FRAME_SAMPLES : int = 960


def send_to_viewers(stream_path : str, data : bytes) -> None:
	global send_start_time

	session = sessions.get(stream_path)

	if not session:
		return

	viewers = session.get('viewers')

	if not viewers:
		return

	if send_start_time == 0:
		send_start_time = _time.monotonic()

	elapsed = _time.monotonic() - send_start_time
	timestamp = int(elapsed * 90000) & 0xFFFFFFFF
	buf = ctypes.create_string_buffer(data)
	data_len = len(data)

	for viewer in viewers:
		if not viewer.get('connected'):
			continue

		for track_id in viewer.get('tracks', []):
			if not lib.rtcIsOpen(track_id):
				continue

			lib.rtcSetTrackRtpTimestamp(track_id, timestamp)
			lib.rtcSendMessage(track_id, buf, data_len)


libopus_handle = None


def init_opus_encoder() -> None:
	global opus_enc, libopus_handle

	if opus_enc:
		return

	libopus_handle = ctypes.CDLL(ctypes.util.find_library('opus'))
	libopus_handle.opus_encoder_create.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
	libopus_handle.opus_encoder_create.restype = ctypes.c_void_p
	libopus_handle.opus_encode.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int32]
	libopus_handle.opus_encode.restype = ctypes.c_int32

	error = ctypes.c_int(0)
	opus_enc = libopus_handle.opus_encoder_create(48000, 2, 2049, ctypes.byref(error))


def encode_opus_frame(pcm_data : bytes) -> Optional[bytes]:
	if not opus_enc or not libopus_handle:
		return None

	max_packet = 4000
	output = (ctypes.c_ubyte * max_packet)()
	result = libopus_handle.opus_encode(opus_enc, pcm_data, OPUS_FRAME_SAMPLES, output, max_packet)

	if result > 0:
		return bytes(output[:result])
	return None


def get_opus_encoder() -> None:
	init_opus_encoder()


def send_audio(stream_path : str, pcm_data : bytes) -> None:
	global audio_pts

	session = sessions.get(stream_path)

	if not session:
		return

	viewers = session.get('viewers')

	if not viewers:
		return

	init_opus_encoder()

	with audio_lock:
		audio_buffer.extend(pcm_data)
		needed = OPUS_FRAME_SAMPLES * 2 * 2

		while len(audio_buffer) >= needed:
			chunk = bytes(audio_buffer[:needed])
			del audio_buffer[:needed]

			opus_data = encode_opus_frame(chunk)

			if not opus_data:
				continue

			buf = ctypes.create_string_buffer(opus_data)

			for viewer in viewers:
				if not viewer.get('connected'):
					continue

				audio_track_id = viewer.get('audio_track')

				if not audio_track_id:
					continue

				if not lib.rtcIsOpen(audio_track_id):
					continue

				lib.rtcSetTrackRtpTimestamp(audio_track_id, audio_pts & 0xFFFFFFFF)
				lib.rtcSendMessage(audio_track_id, buf, len(opus_data))

			audio_pts += OPUS_FRAME_SAMPLES


h264_au_buffer : Dict[str, bytes] = {}


def send_vp8_frame(stream_path : str, frame_data : bytes) -> None:
	send_h264_frame(stream_path, frame_data)


def send_h264_frame(stream_path : str, frame_data : bytes) -> None:
	session = sessions.get(stream_path)

	if not session:
		return

	prev = h264_au_buffer.get(stream_path, b'')
	buf = prev + frame_data

	au_starts = []
	i = 0

	while i < len(buf) - 4:
		if buf[i] == 0 and buf[i + 1] == 0 and buf[i + 2] == 0 and buf[i + 3] == 1 and i + 4 < len(buf):
			nal_type = buf[i + 4] & 0x1f

			if nal_type == 7 or nal_type == 5:
				au_starts.append(i)

		i += 1

	if len(au_starts) < 2:
		h264_au_buffer[stream_path] = buf
		return

	for j in range(len(au_starts) - 1):
		au = buf[au_starts[j]:au_starts[j + 1]]

		for viewer in session.get('viewers', []):
			tracks = viewer.get('tracks', [])

			if tracks:
				lib.rtcSendMessage(tracks[0], au, len(au))

	h264_au_buffer[stream_path] = buf[au_starts[-1]:]


def destroy_session(stream_path : str) -> None:
	session = sessions.pop(stream_path, None)

	if not session:
		return

	for viewer in session.get('viewers', []):
		pc_id = viewer.get('pc')

		if pc_id is not None:
			lib.rtcDeletePeerConnection(pc_id)


def send_data(stream_path : str, data : bytes) -> None:
	session = sessions.get(stream_path)

	if not session:
		return

	for viewer in session.get('viewers', []):
		for track_id in viewer.get('tracks', []):
			lib.rtcSendMessage(track_id, data, len(data))


def handle_whep_offer(stream_path : str, sdp_offer : str) -> Optional[str]:
	session = sessions.get(stream_path)

	if not session:
		return None

	if not lib:
		return None

	pc = create_peer_connection()
	gathering_done = threading.Event()
	local_sdp_holder = [None]

	def on_description(pc_id, sdp, type_str, user_ptr):
		local_sdp_holder[0] = sdp.decode('utf-8') if sdp else None

	def on_candidate(pc_id, candidate, mid, user_ptr):
		pass

	def on_gathering(pc_id, state, user_ptr):
		if state == RTC_GATHERING_COMPLETE:
			gathering_done.set()

	viewer = {'pc': pc, 'tracks': [], 'connected': False}

	def on_state(pc_id, state, user_ptr):
		if state == RTC_CONNECTED:
			viewer['connected'] = True
			logger.info('viewer pc connected', __name__)

	desc_cb = DESCRIPTION_CALLBACK_TYPE(on_description)
	cand_cb = CANDIDATE_CALLBACK_TYPE(on_candidate)
	gather_cb = GATHERING_CALLBACK_TYPE(on_gathering)
	state_cb = STATE_CALLBACK_TYPE(on_state)
	callback_refs.extend([desc_cb, cand_cb, gather_cb, state_cb])

	lib.rtcSetLocalDescriptionCallback(pc, desc_cb)
	lib.rtcSetLocalCandidateCallback(pc, cand_cb)
	lib.rtcSetGatheringStateChangeCallback(pc, gather_cb)
	lib.rtcSetStateChangeCallback(pc, state_cb)

	video_sdp = b'm=video 9 UDP/TLS/RTP/SAVPF 96\r\na=rtpmap:96 VP8/90000\r\na=sendonly\r\na=mid:0\r\na=rtcp-mux\r\n'
	audio_sdp = b'm=audio 9 UDP/TLS/RTP/SAVPF 111\r\na=rtpmap:111 opus/48000/2\r\na=sendonly\r\na=mid:1\r\na=rtcp-mux\r\n'

	video_track = lib.rtcAddTrack(pc, video_sdp)
	audio_track = lib.rtcAddTrack(pc, audio_sdp)

	video_packetizer = RtcPacketizerInit()
	video_packetizer.ssrc = 42
	video_packetizer.cname = b'video'
	video_packetizer.payloadType = 96
	video_packetizer.clockRate = 90000
	video_packetizer.maxFragmentSize = 1200
	lib.rtcSetVP8Packetizer(video_track, ctypes.byref(video_packetizer))
	lib.rtcChainRtcpSrReporter(video_track)
	lib.rtcChainRtcpNackResponder(video_track, 512)

	audio_packetizer = RtcPacketizerInit()
	audio_packetizer.ssrc = 43
	audio_packetizer.cname = b'audio'
	audio_packetizer.payloadType = 111
	audio_packetizer.clockRate = 48000
	lib.rtcSetOpusPacketizer(audio_track, ctypes.byref(audio_packetizer))
	lib.rtcChainRtcpSrReporter(audio_track)

	viewer['tracks'] = [video_track]
	viewer['audio_track'] = audio_track
	session['viewers'].append(viewer)

	lib.rtcSetRemoteDescription(pc, sdp_offer.encode('utf-8'), b'offer')

	gathering_done.wait(timeout = 3)

	buf_size = 16384
	buf = ctypes.create_string_buffer(buf_size)
	result = lib.rtcGetLocalDescription(pc, buf, buf_size)

	if result > 0:
		local_sdp = buf.value.decode('utf-8')
	elif local_sdp_holder[0]:
		local_sdp = local_sdp_holder[0]
	else:
		session['viewers'].remove(viewer)
		return None

	return local_sdp


def start() -> None:
	global running, http_thread

	if not load_library():
		return

	running = True
	http_thread = threading.Thread(target = run_http_server, daemon = True)
	http_thread.start()
	logger.info('rtc whep server started on port ' + str(WHEP_PORT), __name__)


def stop() -> None:
	global running

	running = False

	for stream_path in list(sessions.keys()):
		destroy_session(stream_path)


def run_http_server() -> None:
	class WhepHandler(BaseHTTPRequestHandler):
		def log_message(self, format, *args) -> None:
			pass

		def send_cors_headers(self) -> None:
			self.send_header('Access-Control-Allow-Origin', '*')
			self.send_header('Access-Control-Allow-Methods', 'POST, DELETE, OPTIONS')
			self.send_header('Access-Control-Allow-Headers', 'Content-Type')

		def do_OPTIONS(self) -> None:
			self.send_response(200)
			self.send_cors_headers()
			self.end_headers()

		def do_POST(self) -> None:
			path = self.path

			if not path.endswith('/whep'):
				self.send_response(404)
				self.send_cors_headers()
				self.end_headers()
				return

			stream_path = path[1:].rsplit('/whep', 1)[0]
			content_length = int(self.headers.get('Content-Length', 0))
			body = self.rfile.read(content_length).decode('utf-8') if content_length else ''
			answer = handle_whep_offer(stream_path, body)

			if answer:
				self.send_response(201)
				self.send_header('Content-Type', 'application/sdp')
				self.send_header('Location', path)
				self.send_cors_headers()
				self.end_headers()
				self.wfile.write(answer.encode('utf-8'))
				return

			self.send_response(404)
			self.send_cors_headers()
			self.end_headers()

	server = HTTPServer(('0.0.0.0', WHEP_PORT), WhepHandler)
	server.timeout = 1

	while running:
		server.handle_request()
