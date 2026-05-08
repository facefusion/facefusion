import ctypes
from functools import lru_cache
from typing import Dict, Optional

from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.filesystem import resolve_relative_path
from facefusion.types import DownloadSet

LOG_CB_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p)


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


def resolve_binary_file() -> Optional[str]:
	if is_linux():
		return 'linux-x64-openssl-h264-vp8-av1-opus-libdatachannel-0.24.1.so'
	if is_macos():
		return 'macos-universal-openssl-h264-vp8-av1-opus-libdatachannel-0.24.1.dylib'
	if is_windows():
		return 'windows-x64-openssl-h264-vp8-av1-opus-datachannel-0.24.1.dll'
	return None


def create_rtc_configuration() -> ctypes.Structure:
	return type('RTC_CONFIGURATION', (ctypes.Structure,),
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
	})()


def create_rtc_packetizer_init() -> ctypes.Structure:
	return type('RTC_PACKETIZER_INIT', (ctypes.Structure,),
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
	})()


@lru_cache
def create_static_datachannel_library() -> Optional[ctypes.CDLL]:
	binary_path = create_static_download_set().get('sources').get('datachannel').get('path')

	if binary_path:
		datachannel_library = ctypes.CDLL(binary_path)
		return init_ctypes(datachannel_library)

	return None


def init_ctypes(datachannel_library : ctypes.CDLL) -> ctypes.CDLL:
	datachannel_library.rtcInitLogger.argtypes = [ ctypes.c_int, LOG_CB_TYPE ]
	datachannel_library.rtcInitLogger.restype = None
	datachannel_library.rtcInitLogger(4, LOG_CB_TYPE(0))

	datachannel_library.rtcCreatePeerConnection.restype = ctypes.c_int

	datachannel_library.rtcDeletePeerConnection.argtypes = [ ctypes.c_int ]
	datachannel_library.rtcDeletePeerConnection.restype = ctypes.c_int

	datachannel_library.rtcSetLocalDescription.argtypes = [ ctypes.c_int, ctypes.c_char_p ]
	datachannel_library.rtcSetLocalDescription.restype = ctypes.c_int

	datachannel_library.rtcSetRemoteDescription.argtypes = [ ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p ]
	datachannel_library.rtcSetRemoteDescription.restype = ctypes.c_int

	datachannel_library.rtcAddTrack.argtypes = [ ctypes.c_int, ctypes.c_char_p ]
	datachannel_library.rtcAddTrack.restype = ctypes.c_int

	datachannel_library.rtcSendMessage.argtypes = [ ctypes.c_int, ctypes.c_void_p, ctypes.c_int ]
	datachannel_library.rtcSendMessage.restype = ctypes.c_int

	datachannel_library.rtcSetVP8Packetizer.restype = ctypes.c_int

	datachannel_library.rtcChainRtcpSrReporter.argtypes = [ ctypes.c_int ]
	datachannel_library.rtcChainRtcpSrReporter.restype = ctypes.c_int

	datachannel_library.rtcSetTrackRtpTimestamp.argtypes = [ ctypes.c_int, ctypes.c_uint32 ]
	datachannel_library.rtcSetTrackRtpTimestamp.restype = ctypes.c_int

	datachannel_library.rtcIsOpen.argtypes = [ ctypes.c_int ]
	datachannel_library.rtcIsOpen.restype = ctypes.c_bool

	datachannel_library.rtcChainRtcpNackResponder.argtypes = [ ctypes.c_int, ctypes.c_uint ]
	datachannel_library.rtcChainRtcpNackResponder.restype = ctypes.c_int

	datachannel_library.rtcGetLocalDescription.argtypes = [ ctypes.c_int, ctypes.c_char_p, ctypes.c_int ]
	datachannel_library.rtcGetLocalDescription.restype = ctypes.c_int

	datachannel_library.rtcSetLocalDescription.argtypes = [ ctypes.c_int, ctypes.c_char_p ]
	datachannel_library.rtcSetLocalDescription.restype = ctypes.c_int

	datachannel_library.rtcSetOpusPacketizer.restype = ctypes.c_int

	datachannel_library.rtcSetUserPointer.argtypes = [ ctypes.c_int, ctypes.c_void_p ]
	datachannel_library.rtcSetUserPointer.restype = None

	datachannel_library.rtcSetLocalDescriptionCallback.argtypes = [ ctypes.c_int, ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p) ]
	datachannel_library.rtcSetLocalDescriptionCallback.restype = ctypes.c_int

	datachannel_library.rtcSetGatheringStateChangeCallback.argtypes = [ ctypes.c_int, ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p) ]
	datachannel_library.rtcSetGatheringStateChangeCallback.restype = ctypes.c_int

	datachannel_library.rtcSetStateChangeCallback.argtypes = [ ctypes.c_int, ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p) ]
	datachannel_library.rtcSetStateChangeCallback.restype = ctypes.c_int

	return datachannel_library
