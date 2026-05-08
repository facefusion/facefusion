import ctypes
from functools import lru_cache
from typing import Dict, Optional

from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.filesystem import resolve_relative_path
from facefusion.types import DownloadSet

LOG_CB_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p)


def create_rtc_configuration() -> ctypes.Structure:
	rtc_configuration = type('RTC_CONFIGURATION', (ctypes.Structure,),
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
	return rtc_configuration()


def create_rtc_packetizer_init() -> ctypes.Structure:
	rtc_packetizer_init = type('RTC_PACKETIZER_INIT', (ctypes.Structure,),
	{
		'_fields_':
		[
			('ssrc', ctypes.c_uint32),
			('cname', ctypes.c_char_p),
			('payloadType', ctypes.c_uint8),
			('clockRate', ctypes.c_uint32),
			('sequenceNumber', ctypes.c_uint16),
			('timestamp', ctypes.c_uint32),
			('maxFragmentSize', ctypes.c_uint16)
		]
	})
	return rtc_packetizer_init()


def resolve_binary_file() -> Optional[str]:
	if is_linux():
		return 'linux-x64-openssl-h264-vp8-av1-opus-libdatachannel-0.24.1.so'
	if is_macos():
		return 'macos-universal-openssl-h264-vp8-av1-opus-libdatachannel-0.24.1.dylib'
	if is_windows():
		return 'windows-x64-openssl-h264-vp8-av1-opus-datachannel-0.24.1.dll'
	return None


@lru_cache
def create_static_download_set() -> Dict[str, DownloadSet]: # TODO: replace once conda package is in place
	binary_name = resolve_binary_file()

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


@lru_cache
def create_static_rtc_library() -> Optional[ctypes.CDLL]:
	binary_path = create_static_download_set().get('sources').get('datachannel').get('path')

	if binary_path:
		rtc_library = ctypes.CDLL(binary_path)
		return init_ctypes(rtc_library)

	return None


def init_ctypes(rtc_library : ctypes.CDLL) -> ctypes.CDLL:
	rtc_library.rtcInitLogger.argtypes = [ ctypes.c_int, LOG_CB_TYPE ]
	rtc_library.rtcInitLogger.restype = None
	rtc_library.rtcInitLogger(4, LOG_CB_TYPE(0))

	rtc_library.rtcCreatePeerConnection.restype = ctypes.c_int

	rtc_library.rtcDeletePeerConnection.argtypes = [ ctypes.c_int ]
	rtc_library.rtcDeletePeerConnection.restype = ctypes.c_int

	rtc_library.rtcSetLocalDescription.argtypes = [ ctypes.c_int, ctypes.c_char_p ]
	rtc_library.rtcSetLocalDescription.restype = ctypes.c_int

	rtc_library.rtcSetRemoteDescription.argtypes = [ ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p ]
	rtc_library.rtcSetRemoteDescription.restype = ctypes.c_int

	rtc_library.rtcAddTrack.argtypes = [ ctypes.c_int, ctypes.c_char_p ]
	rtc_library.rtcAddTrack.restype = ctypes.c_int

	rtc_library.rtcSendMessage.argtypes = [ ctypes.c_int, ctypes.c_void_p, ctypes.c_int ]
	rtc_library.rtcSendMessage.restype = ctypes.c_int

	rtc_library.rtcSetVP8Packetizer.restype = ctypes.c_int

	rtc_library.rtcChainRtcpSrReporter.argtypes = [ ctypes.c_int ]
	rtc_library.rtcChainRtcpSrReporter.restype = ctypes.c_int

	rtc_library.rtcSetTrackRtpTimestamp.argtypes = [ ctypes.c_int, ctypes.c_uint32 ]
	rtc_library.rtcSetTrackRtpTimestamp.restype = ctypes.c_int

	rtc_library.rtcIsOpen.argtypes = [ ctypes.c_int ]
	rtc_library.rtcIsOpen.restype = ctypes.c_bool

	rtc_library.rtcChainRtcpNackResponder.argtypes = [ ctypes.c_int, ctypes.c_uint ]
	rtc_library.rtcChainRtcpNackResponder.restype = ctypes.c_int

	rtc_library.rtcGetLocalDescription.argtypes = [ ctypes.c_int, ctypes.c_char_p, ctypes.c_int ]
	rtc_library.rtcGetLocalDescription.restype = ctypes.c_int

	rtc_library.rtcSetLocalDescription.argtypes = [ ctypes.c_int, ctypes.c_char_p ]
	rtc_library.rtcSetLocalDescription.restype = ctypes.c_int

	rtc_library.rtcSetOpusPacketizer.restype = ctypes.c_int

	return rtc_library
