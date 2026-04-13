import ctypes
import ctypes.util
import threading
import time
from functools import lru_cache
from typing import Dict, Optional, Tuple

from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.filesystem import resolve_relative_path
from facefusion.types import DownloadSet, RtcAudioTrack, RtcPeer, RtcStateValue, RtcVideoTrack

RTC_CONFIGURATION = type('RtcConfiguration', (ctypes.Structure,),
{
	'_fields_':
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
})

RTC_PACKETIZER_INIT = type('RtcPacketizerInit', (ctypes.Structure,),
{
	'_fields_':
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
})

RTC_STATE : Dict[str, RtcStateValue] =\
{
	'lib': None,
	'sessions': {},
	'pending_connections': {},
	'send_start_time': 0.0,
	'audio_pts': 0,
	'opus_enc': None,
	'libopus_handle': None,
	'audio_buffer': bytearray(),
	'audio_lock': threading.Lock(),
	'desc_cb': None,
	'gather_cb': None,
	'state_cb': None
}


def resolve_binary_name() -> Optional[str]:
	if is_linux():
		return 'linux-x64-openssl-h264-vp8-av1-opus-libdatachannel-0.24.1.so'
	if is_macos():
		return 'macos-universal-openssl-h264-vp8-av1-opus-libdatachannel-0.24.1.dylib'
	if is_windows():
		return 'windows-x64-openssl-h264-vp8-av1-opus-datachannel-0.24.1.dll'
	return None


@lru_cache
def create_static_download_set() -> Dict[str, DownloadSet]:
	binary_name = resolve_binary_name()

	return\
	{
		'hashes':
		{
			'datachannel':
			{
				'url': resolve_download_url('binaries-1.0.0', binary_name + '.hash'),
				'path': resolve_relative_path('../.assets/binaries/' + binary_name + '.hash')
			}
		},
		'sources':
		{
			'datachannel':
			{
				'url': resolve_download_url('binaries-1.0.0', binary_name),
				'path': resolve_relative_path('../.assets/binaries/' + binary_name)
			}
		}
	}


def pre_check() -> bool:
	download_set = create_static_download_set()

	if not conditional_download_hashes(download_set.get('hashes')):
		return False
	return conditional_download_sources(download_set.get('sources'))


def on_description(peer_connection_id : int, local_sdp_bytes : Optional[bytes], type_str : Optional[bytes], user_ptr : Optional[int]) -> None:
	pending_connection = RTC_STATE['pending_connections'].get(peer_connection_id)

	if pending_connection:
		pending_connection['local_sdp'] = local_sdp_bytes and local_sdp_bytes.decode('utf-8')


def on_gathering(peer_connection_id : int, gathering_state : int, user_ptr : Optional[int]) -> None:
	pending_connection = RTC_STATE['pending_connections'].get(peer_connection_id)

	if pending_connection and gathering_state == 2:
		pending_connection['ice_gather'].set()


def on_state(peer_connection_id : int, connection_state : int, user_ptr : Optional[int]) -> None:
	if connection_state == 2:

		for session in RTC_STATE.get('sessions').values():
			for rtc_peer in session.get('peers', []):
				if rtc_peer.get('pc') == peer_connection_id:
					rtc_peer['connected'] = True
					return None
	return None


def load_library() -> bool:
	binary_path = create_static_download_set().get('sources').get('datachannel').get('path')

	if binary_path:
		RTC_STATE['lib'] = ctypes.CDLL(binary_path)
		prepare_types()
		return True

	return False


def prepare_types() -> None:
	rtc_library = RTC_STATE.get('lib')
	log_cb_type = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p)
	desc_cb_type = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p)
	state_cb_type = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)
	gather_cb_type = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)
	rtc_library.rtcInitLogger.argtypes = [ ctypes.c_int, log_cb_type ]
	rtc_library.rtcInitLogger.restype = None
	rtc_library.rtcInitLogger(4, log_cb_type(0))

	rtc_library.rtcCreatePeerConnection.argtypes = [ctypes.POINTER(RTC_CONFIGURATION)]
	rtc_library.rtcCreatePeerConnection.restype = ctypes.c_int

	rtc_library.rtcDeletePeerConnection.argtypes = [ ctypes.c_int ]
	rtc_library.rtcDeletePeerConnection.restype = ctypes.c_int

	rtc_library.rtcSetRemoteDescription.argtypes = [ ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p ]
	rtc_library.rtcSetRemoteDescription.restype = ctypes.c_int

	rtc_library.rtcAddTrack.argtypes = [ ctypes.c_int, ctypes.c_char_p ]
	rtc_library.rtcAddTrack.restype = ctypes.c_int

	rtc_library.rtcSetLocalDescriptionCallback.argtypes = [ ctypes.c_int, desc_cb_type ]
	rtc_library.rtcSetLocalDescriptionCallback.restype = ctypes.c_int

	rtc_library.rtcSetStateChangeCallback.argtypes = [ ctypes.c_int, state_cb_type ]
	rtc_library.rtcSetStateChangeCallback.restype = ctypes.c_int

	rtc_library.rtcSetGatheringStateChangeCallback.argtypes = [ ctypes.c_int, gather_cb_type ]
	rtc_library.rtcSetGatheringStateChangeCallback.restype = ctypes.c_int

	rtc_library.rtcSendMessage.argtypes = [ ctypes.c_int, ctypes.c_void_p, ctypes.c_int ]
	rtc_library.rtcSendMessage.restype = ctypes.c_int

	rtc_library.rtcSetVP8Packetizer.argtypes = [ctypes.c_int, ctypes.POINTER(RTC_PACKETIZER_INIT)]
	rtc_library.rtcSetVP8Packetizer.restype = ctypes.c_int

	rtc_library.rtcChainRtcpSrReporter.argtypes = [ ctypes.c_int ]
	rtc_library.rtcChainRtcpSrReporter.restype = ctypes.c_int

	rtc_library.rtcSetTrackRtpTimestamp.argtypes = [ ctypes.c_int, ctypes.c_uint32 ]
	rtc_library.rtcSetTrackRtpTimestamp.restype = ctypes.c_int

	rtc_library.rtcIsOpen.argtypes = [ ctypes.c_int ]
	rtc_library.rtcIsOpen.restype = ctypes.c_bool

	rtc_library.rtcSetOpusPacketizer.argtypes = [ctypes.c_int, ctypes.POINTER(RTC_PACKETIZER_INIT)]
	rtc_library.rtcSetOpusPacketizer.restype = ctypes.c_int

	RTC_STATE['desc_cb'] = desc_cb_type(on_description)
	RTC_STATE['gather_cb'] = gather_cb_type(on_gathering)
	RTC_STATE['state_cb'] = state_cb_type(on_state)


def create_peer_connection() -> int:
	config = RTC_CONFIGURATION()
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
	return RTC_STATE.get('lib').rtcCreatePeerConnection(ctypes.byref(config))


def create_session(stream_path : str) -> None:
	RTC_STATE.get('sessions')[stream_path] =\
	{
		'peers': []
	}


def send_to_peers(stream_path : str, data : bytes) -> None:
	session = RTC_STATE.get('sessions').get(stream_path)

	if session:
		peers = session.get('peers')

		if peers:
			if RTC_STATE.get('send_start_time') == 0:
				RTC_STATE['send_start_time'] = time.monotonic()

			timestamp = int(time.monotonic() - RTC_STATE.get('send_start_time') * 90000) & 0xFFFFFFFF
			data_buffer = ctypes.create_string_buffer(data)
			data_total = len(data)

			for rtc_peer in peers:
				if rtc_peer.get('connected'):
					video_track_id = rtc_peer.get('video_track')

					if video_track_id and RTC_STATE.get('lib').rtcIsOpen(video_track_id):
						RTC_STATE.get('lib').rtcSetTrackRtpTimestamp(video_track_id, timestamp)
						RTC_STATE.get('lib').rtcSendMessage(video_track_id, data_buffer, data_total)

	return None


def init_opus_encoder() -> bool:
	if RTC_STATE.get('opus_enc'):
		return True

	opus_path = ctypes.util.find_library('opus')

	if opus_path:
		RTC_STATE['libopus_handle'] = ctypes.CDLL(opus_path)
		RTC_STATE.get('libopus_handle').opus_encoder_create.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
		RTC_STATE.get('libopus_handle').opus_encoder_create.restype = ctypes.c_void_p
		RTC_STATE.get('libopus_handle').opus_encode.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int32]
		RTC_STATE.get('libopus_handle').opus_encode.restype = ctypes.c_int32
		RTC_STATE['opus_enc'] = RTC_STATE.get('libopus_handle').opus_encoder_create(48000, 2, 2049, ctypes.byref(ctypes.c_int(0)))
		return True

	return False


def encode_opus_frame(pcm_data : bytes) -> Optional[bytes]:
	opus_enc = RTC_STATE.get('opus_enc')
	libopus_handle = RTC_STATE.get('libopus_handle')

	if opus_enc and libopus_handle:
		max_packet = 4000
		opus_buffer = (ctypes.c_ubyte * max_packet)()
		encode_size = libopus_handle.opus_encode(opus_enc, pcm_data, 960, opus_buffer, max_packet)

		if encode_size > 0:
			return bytes(opus_buffer[:encode_size])

	return None


def send_audio(stream_path : str, pcm_data : bytes) -> None:
	session = RTC_STATE.get('sessions').get(stream_path)

	if session:
		peers = session.get('peers')

		if peers:
			init_opus_encoder()
			rtc_library = RTC_STATE.get('lib')

			with RTC_STATE.get('audio_lock'):
				RTC_STATE.get('audio_buffer').extend(pcm_data)
				pcm_frame_size = 960 * 2 * 2

				while len(RTC_STATE.get('audio_buffer')) >= pcm_frame_size:
					chunk = bytes(RTC_STATE.get('audio_buffer')[:pcm_frame_size])
					del RTC_STATE.get('audio_buffer')[:pcm_frame_size]

					opus_data = encode_opus_frame(chunk)

					if not opus_data:
						continue

					encoded_audio_buffer = ctypes.create_string_buffer(opus_data)

					for rtc_peer in peers:
						if not rtc_peer.get('connected'):
							continue

						audio_track_id = rtc_peer.get('audio_track')

						if not audio_track_id:
							continue

						if not rtc_library.rtcIsOpen(audio_track_id):
							continue

						rtc_library.rtcSetTrackRtpTimestamp(audio_track_id, RTC_STATE.get('audio_pts') & 0xFFFFFFFF)
						rtc_library.rtcSendMessage(audio_track_id, encoded_audio_buffer, len(opus_data))

					RTC_STATE['audio_pts'] += 960

	return None


def destroy_session(stream_path : str) -> None:
	session = RTC_STATE.get('sessions').pop(stream_path, None)
	rtc_library = RTC_STATE.get('lib')

	if session:
		for rtc_peer in session.get('peers'):
			peer_connection_id = rtc_peer.get('pc')

			if peer_connection_id is not None:
				rtc_library.rtcDeletePeerConnection(peer_connection_id)


def register_pending_connection(peer_connection : int) -> threading.Event:
	ice_gather = threading.Event()
	rtc_library = RTC_STATE.get('lib')

	RTC_STATE['pending_connections'][peer_connection] =\
	{
		'ice_gather': ice_gather,
		'local_sdp': None
	}

	rtc_library.rtcSetLocalDescriptionCallback(peer_connection, RTC_STATE.get('desc_cb'))
	rtc_library.rtcSetGatheringStateChangeCallback(peer_connection, RTC_STATE.get('gather_cb'))
	rtc_library.rtcSetStateChangeCallback(peer_connection, RTC_STATE.get('state_cb'))
	return ice_gather


def add_media_tracks(peer_connection : int) -> Tuple[RtcVideoTrack, RtcAudioTrack]:
	rtc_library = RTC_STATE.get('lib')

	video_media_description = b'm=video 9 UDP/TLS/RTP/SAVPF 96\r\na=rtpmap:96 VP8/90000\r\na=sendonly\r\na=mid:0\r\na=rtcp-mux\r\n'
	audio_media_description = b'm=audio 9 UDP/TLS/RTP/SAVPF 111\r\na=rtpmap:111 opus/48000/2\r\na=sendonly\r\na=mid:1\r\na=rtcp-mux\r\n'

	video_track = rtc_library.rtcAddTrack(peer_connection, video_media_description)
	audio_track = rtc_library.rtcAddTrack(peer_connection, audio_media_description)

	video_packetizer = RTC_PACKETIZER_INIT()
	video_packetizer.ssrc = 42
	video_packetizer.cname = b'video'
	video_packetizer.payloadType = 96
	video_packetizer.clockRate = 90000
	video_packetizer.maxFragmentSize = 1200
	rtc_library.rtcSetVP8Packetizer(video_track, ctypes.byref(video_packetizer))
	rtc_library.rtcChainRtcpSrReporter(video_track)

	audio_packetizer = RTC_PACKETIZER_INIT()
	audio_packetizer.ssrc = 43
	audio_packetizer.cname = b'audio'
	audio_packetizer.payloadType = 111
	audio_packetizer.clockRate = 48000
	rtc_library.rtcSetOpusPacketizer(audio_track, ctypes.byref(audio_packetizer))
	rtc_library.rtcChainRtcpSrReporter(audio_track)
	return video_track, audio_track


def negotiate_sdp(peer_connection : int, sdp_offer : str, ice_gather : threading.Event) -> Optional[str]:
	RTC_STATE.get('lib').rtcSetRemoteDescription(peer_connection, sdp_offer.encode('utf-8'), b'offer')
	ice_gather.wait(timeout = 3)
	pending_connection = RTC_STATE.get('pending_connections').pop(peer_connection, {})
	return pending_connection.get('local_sdp')


def handle_whep_offer(stream_path : str, sdp_offer : str) -> Optional[str]:
	session = RTC_STATE.get('sessions').get(stream_path)
	peer_connection = create_peer_connection()
	ice_gather = register_pending_connection(peer_connection)
	video_track, audio_track = add_media_tracks(peer_connection)

	rtc_peer : RtcPeer =\
	{
		'peer_connection': peer_connection,
		'video_track': video_track,
		'audio_track': audio_track,
		'connection': False
	}
	session['peers'].append(rtc_peer)

	local_sdp = negotiate_sdp(peer_connection, sdp_offer, ice_gather)

	if not local_sdp:
		session['peers'].remove(rtc_peer)

	return local_sdp


def start() -> None:
	load_library()


def stop() -> None:
	for stream_path in list(RTC_STATE.get('sessions').keys()):
		destroy_session(stream_path)
