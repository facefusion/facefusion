import ctypes
import ctypes.util
import os
import threading
import time
from typing import Dict, List, Optional, TypeAlias

from facefusion import logger

RtcLib : TypeAlias = ctypes.CDLL

lib : Optional[RtcLib] = None
sessions : Dict[str, dict] = {}

RTC_CONNECTED = 2
RTC_GATHERING_COMPLETE = 2

LOG_CALLBACK_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p)
DESCRIPTION_CALLBACK_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p)
CANDIDATE_CALLBACK_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p)
STATE_CALLBACK_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)
GATHERING_CALLBACK_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)


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
		('playoutDelayMax', ctypes.c_uint16)
	]


def find_library() -> Optional[str]:
	project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	bin_dir = os.path.join(project_root, 'bin')

	if not os.path.isdir(bin_dir):
		return None

	ext = '.dll' if os.name == 'nt' else '.so'

	for name in os.listdir(bin_dir):
		if 'datachannel' in name and name.endswith(ext):
			return os.path.join(bin_dir, name)

	return None


def load_library() -> bool:
	global lib

	if lib:
		return True

	lib_path = find_library()

	if not lib_path:
		logger.warn('libdatachannel not found', __name__)
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

	lib.rtcSetRemoteDescription.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p]
	lib.rtcSetRemoteDescription.restype = ctypes.c_int

	lib.rtcGetLocalDescription.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
	lib.rtcGetLocalDescription.restype = ctypes.c_int

	lib.rtcAddTrack.argtypes = [ctypes.c_int, ctypes.c_char_p]
	lib.rtcAddTrack.restype = ctypes.c_int

	lib.rtcSetLocalDescriptionCallback.argtypes = [ctypes.c_int, DESCRIPTION_CALLBACK_TYPE]
	lib.rtcSetLocalDescriptionCallback.restype = ctypes.c_int

	lib.rtcSetLocalCandidateCallback.argtypes = [ctypes.c_int, CANDIDATE_CALLBACK_TYPE]
	lib.rtcSetLocalCandidateCallback.restype = ctypes.c_int

	lib.rtcSetStateChangeCallback.argtypes = [ctypes.c_int, STATE_CALLBACK_TYPE]
	lib.rtcSetStateChangeCallback.restype = ctypes.c_int

	lib.rtcSetGatheringStateChangeCallback.argtypes = [ctypes.c_int, GATHERING_CALLBACK_TYPE]
	lib.rtcSetGatheringStateChangeCallback.restype = ctypes.c_int

	lib.rtcSendMessage.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
	lib.rtcSendMessage.restype = ctypes.c_int

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


def create_session(stream_path : str) -> None:
	sessions[stream_path] = {'viewers': []}


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
		send_start_time = time.monotonic()

	elapsed = time.monotonic() - send_start_time
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

	opus_path = ctypes.util.find_library('opus')

	if not opus_path:
		if not hasattr(init_opus_encoder, '_warned'):
			logger.warn('libopus not found, audio encoding disabled', __name__)
			init_opus_encoder._warned = True
		return

	libopus_handle = ctypes.CDLL(opus_path)
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


def destroy_session(stream_path : str) -> None:
	session = sessions.pop(stream_path, None)

	for viewer in session.get('viewers', []):
		pc_id = viewer.get('pc')

		if pc_id is not None:
			lib.rtcDeletePeerConnection(pc_id)


def handle_whep_offer(stream_path : str, sdp_offer : str) -> Optional[str]:
	session = sessions.get(stream_path)
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

	def on_track_open(track_id, user_ptr):
		logger.info('track ' + str(track_id) + ' opened', __name__)

	track_open_cb = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_void_p)(on_track_open)
	callback_refs.append(track_open_cb)
	lib.rtcSetOpenCallback(video_track, track_open_cb)

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
	load_library()


def stop() -> None:
	for stream_path in list(sessions.keys()):
		destroy_session(stream_path)
