import ctypes
import ctypes.util
import threading
from functools import lru_cache
from typing import Dict, Optional

from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.filesystem import resolve_relative_path
from facefusion.types import DownloadSet, RtcStateValue

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
	'library': None,
	'sessions': {},
	'pending_connections': {},
	'send_start_time': 0.0,
	'audio_timestamp': 0,
	'opus_encoder': None,
	'opus_library': None,
	'audio_buffer': bytearray(),
	'audio_lock': threading.Lock(),
	'description_callback': None,
	'gathering_callback': None,
	'state_callback': None,
	'track_open_callback': None
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
				'url': 'https://huggingface.co/bluefoxcreation/libdatachannel/resolve/main/linux-x64-openssl-h264-vp8-av1-opus-libdatachannel-0.24.1.so.hash', # TODO: use url with dynamic binary_name
				'path': resolve_relative_path('../.assets/binaries/' + binary_name + '.hash')
			}
		},
		'sources':
		{
			'datachannel':
			{
				'url': 'https://huggingface.co/bluefoxcreation/libdatachannel/resolve/main/linux-x64-openssl-h264-vp8-av1-opus-libdatachannel-0.24.1.so', # TODO: use url with dynamic binary_name
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
	pending_connection = RTC_STATE.get('pending_connections').get(peer_connection_id)

	if pending_connection:
		pending_connection['local_sdp'] = local_sdp_bytes and local_sdp_bytes.decode('utf-8')


def on_gathering(peer_connection_id : int, gathering_state : int, user_ptr : Optional[int]) -> None:
	pending_connection = RTC_STATE.get('pending_connections').get(peer_connection_id)

	if pending_connection and gathering_state == 2:
		pending_connection['ice_gather'].set()


def on_track_open(track_id : int, user_ptr : Optional[int]) -> None:
	pass


def on_state(peer_connection_id : int, connection_state : int, user_ptr : Optional[int]) -> None:
	if connection_state == 2:

		for session in RTC_STATE.get('sessions').values():
			for rtc_peer in session.get('peers', []):
				if rtc_peer.get('pc') == peer_connection_id:
					rtc_peer['connection'] = True
					return None
	return None


def prepare_types() -> None:
	rtc_library = RTC_STATE.get('library')
	log_cb_type = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p)
	desc_cb_type = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p)
	state_cb_type = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)
	gather_cb_type = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)
	open_cb_type = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_void_p)
	rtc_library.rtcInitLogger.argtypes = [ ctypes.c_int, log_cb_type ]
	rtc_library.rtcInitLogger.restype = None
	rtc_library.rtcInitLogger(4, log_cb_type(0))

	rtc_library.rtcCreatePeerConnection.argtypes = [ ctypes.POINTER(RTC_CONFIGURATION) ]
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

	rtc_library.rtcSetVP8Packetizer.argtypes = [ ctypes.c_int, ctypes.POINTER(RTC_PACKETIZER_INIT) ]
	rtc_library.rtcSetVP8Packetizer.restype = ctypes.c_int

	rtc_library.rtcChainRtcpSrReporter.argtypes = [ ctypes.c_int ]
	rtc_library.rtcChainRtcpSrReporter.restype = ctypes.c_int

	rtc_library.rtcSetTrackRtpTimestamp.argtypes = [ ctypes.c_int, ctypes.c_uint32 ]
	rtc_library.rtcSetTrackRtpTimestamp.restype = ctypes.c_int

	rtc_library.rtcIsOpen.argtypes = [ ctypes.c_int ]
	rtc_library.rtcIsOpen.restype = ctypes.c_bool

	rtc_library.rtcSetOpenCallback.argtypes = [ ctypes.c_int, open_cb_type ]
	rtc_library.rtcSetOpenCallback.restype = ctypes.c_int

	rtc_library.rtcChainRtcpNackResponder.argtypes = [ ctypes.c_int, ctypes.c_uint ]
	rtc_library.rtcChainRtcpNackResponder.restype = ctypes.c_int

	rtc_library.rtcGetLocalDescription.argtypes = [ ctypes.c_int, ctypes.c_char_p, ctypes.c_int ]
	rtc_library.rtcGetLocalDescription.restype = ctypes.c_int

	rtc_library.rtcSetOpusPacketizer.argtypes = [ ctypes.c_int, ctypes.POINTER(RTC_PACKETIZER_INIT) ]
	rtc_library.rtcSetOpusPacketizer.restype = ctypes.c_int

	RTC_STATE['description_callback'] = desc_cb_type(on_description)
	RTC_STATE['gathering_callback'] = gather_cb_type(on_gathering)
	RTC_STATE['state_callback'] = state_cb_type(on_state)
	RTC_STATE['track_open_callback'] = open_cb_type(on_track_open)


def init_opus_encoder() -> bool:
	if RTC_STATE.get('opus_encoder'):
		return True

	opus_path = ctypes.util.find_library('opus')

	if opus_path:
		RTC_STATE['opus_library'] = ctypes.CDLL(opus_path)
		RTC_STATE.get('opus_library').opus_encoder_create.argtypes = [ ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int) ]
		RTC_STATE.get('opus_library').opus_encoder_create.restype = ctypes.c_void_p
		RTC_STATE.get('opus_library').opus_encode.argtypes = [ ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int32 ]
		RTC_STATE.get('opus_library').opus_encode.restype = ctypes.c_int32
		RTC_STATE['opus_encoder'] = RTC_STATE.get('opus_library').opus_encoder_create(48000, 2, 2049, ctypes.byref(ctypes.c_int(0)))
		return True

	return False


def encode_opus_frame(pcm_data : bytes) -> Optional[bytes]:
	opus_enc = RTC_STATE.get('opus_encoder')
	libopus_handle = RTC_STATE.get('opus_library')

	if opus_enc and libopus_handle:
		max_packet = 4000
		opus_buffer = (ctypes.c_ubyte * max_packet)()
		encode_size = libopus_handle.opus_encode(opus_enc, pcm_data, 960, opus_buffer, max_packet)

		if encode_size > 0:
			return bytes(opus_buffer[:encode_size])

	return None
