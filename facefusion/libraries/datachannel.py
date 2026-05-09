import ctypes
from functools import lru_cache
from typing import Dict, Optional

from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.filesystem import resolve_relative_path
from facefusion.types import DownloadSet


def resolve_library_file() -> Optional[str]:
	if is_linux():
		return 'linux-x64-openssl-h264-vp8-av1-opus-libdatachannel-0.24.1.so'
	if is_macos():
		return 'macos-universal-openssl-h264-vp8-av1-opus-libdatachannel-0.24.1.dylib'
	if is_windows():
		return 'windows-x64-openssl-h264-vp8-av1-opus-datachannel-0.24.1.dll'
	return None


@lru_cache
def create_static_library_set() -> Dict[str, DownloadSet]:
	library_file = resolve_library_file()

	return\
	{
		'hashes':
		{
			'datachannel':
			{
				'url': 'https://huggingface.co/bluefoxcreation/libdatachannel/resolve/main/linux-x64-openssl-h264-vp8-av1-opus-libdatachannel-0.24.1.so.hash',
				'path': resolve_relative_path('../.binaries/' + library_file + '.hash')
			}
		},
		'sources':
		{
			'datachannel':
			{
				'url': 'https://huggingface.co/bluefoxcreation/libdatachannel/resolve/main/linux-x64-openssl-h264-vp8-av1-opus-libdatachannel-0.24.1.so',
				'path': resolve_relative_path('../.binaries/' + library_file)
			}
		}
	}


@lru_cache
def create_static_library() -> Optional[ctypes.CDLL]:
	library_path = create_static_library_set().get('sources').get('datachannel').get('path')

	if library_path:
		library = ctypes.CDLL(library_path)

		if library:
			return init_ctypes(library)

	return None


def init_ctypes(library : ctypes.CDLL) -> ctypes.CDLL:
	library.rtcInitLogger.argtypes = [ ctypes.c_int, ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p) ]
	library.rtcInitLogger.restype = None
	library.rtcInitLogger(4, ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p)(0))

	library.rtcCreatePeerConnection.restype = ctypes.c_int

	library.rtcDeletePeerConnection.argtypes = [ ctypes.c_int ]
	library.rtcDeletePeerConnection.restype = ctypes.c_int

	library.rtcSetLocalDescription.argtypes = [ ctypes.c_int, ctypes.c_char_p ]
	library.rtcSetLocalDescription.restype = ctypes.c_int

	library.rtcSetRemoteDescription.argtypes = [ ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p ]
	library.rtcSetRemoteDescription.restype = ctypes.c_int

	library.rtcAddTrack.argtypes = [ ctypes.c_int, ctypes.c_char_p ]
	library.rtcAddTrack.restype = ctypes.c_int

	library.rtcSendMessage.argtypes = [ ctypes.c_int, ctypes.c_void_p, ctypes.c_int ]
	library.rtcSendMessage.restype = ctypes.c_int

	library.rtcSetVP8Packetizer.restype = ctypes.c_int

	library.rtcChainRtcpSrReporter.argtypes = [ ctypes.c_int ]
	library.rtcChainRtcpSrReporter.restype = ctypes.c_int

	library.rtcSetTrackRtpTimestamp.argtypes = [ ctypes.c_int, ctypes.c_uint32 ]
	library.rtcSetTrackRtpTimestamp.restype = ctypes.c_int

	library.rtcIsOpen.argtypes = [ ctypes.c_int ]
	library.rtcIsOpen.restype = ctypes.c_bool

	library.rtcChainRtcpNackResponder.argtypes = [ ctypes.c_int, ctypes.c_uint ]
	library.rtcChainRtcpNackResponder.restype = ctypes.c_int

	library.rtcGetLocalDescription.argtypes = [ ctypes.c_int, ctypes.c_char_p, ctypes.c_int ]
	library.rtcGetLocalDescription.restype = ctypes.c_int

	library.rtcSetLocalDescription.argtypes = [ ctypes.c_int, ctypes.c_char_p ]
	library.rtcSetLocalDescription.restype = ctypes.c_int

	library.rtcSetOpusPacketizer.restype = ctypes.c_int

	library.rtcSetUserPointer.argtypes = [ ctypes.c_int, ctypes.c_void_p ]
	library.rtcSetUserPointer.restype = None

	library.rtcSetLocalDescriptionCallback.argtypes = [ ctypes.c_int, ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p) ]
	library.rtcSetLocalDescriptionCallback.restype = ctypes.c_int

	library.rtcSetGatheringStateChangeCallback.argtypes = [ ctypes.c_int, ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p) ]
	library.rtcSetGatheringStateChangeCallback.restype = ctypes.c_int

	library.rtcSetStateChangeCallback.argtypes = [ ctypes.c_int, ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p) ]
	library.rtcSetStateChangeCallback.restype = ctypes.c_int

	return library


def define_rtc_configuration() -> ctypes.Structure:
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


def define_rtc_packetizer_init() -> ctypes.Structure:
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
