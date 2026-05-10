import ctypes
import os
from functools import lru_cache
from typing import Dict, Optional, Tuple

from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url_by_provider
from facefusion.filesystem import resolve_relative_path
from facefusion.types import DownloadSet


def resolve_library_paths() -> Optional[Tuple[str, str]]:
	if is_linux():
		return 'linux/libdatachannel.hash', 'linux/libdatachannel.so'
	if is_macos():
		return 'macos/libdatachannel.hash', 'macos/libdatachannel.dylib'
	if is_windows():
		return 'windows/datachannel.hash', 'windows/datachannel.dll'
	return None


@lru_cache
def create_static_library_set() -> Dict[str, DownloadSet]:
	library_hash_path, library_source_path = resolve_library_paths()

	return\
	{
		'hashes':
		{
			'datachannel':
			{
				'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', library_hash_path),
				'path': resolve_relative_path('../.libraries/' + os.path.basename(library_hash_path))
			}
		},
		'sources':
		{
			'datachannel':
			{
				'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', library_source_path),
				'path': resolve_relative_path('../.libraries/' + os.path.basename(library_source_path))
			}
		}
	}


def pre_check() -> bool:
	library_hash_set = create_static_library_set().get('hashes')
	library_source_set = create_static_library_set().get('sources')

	return conditional_download_hashes(library_hash_set) and conditional_download_sources(library_source_set)


@lru_cache
def create_static_library() -> Optional[ctypes.CDLL]:
	library_path = create_static_library_set().get('sources').get('datachannel').get('path')

	if library_path:
		if is_windows():
			for dll_dir in [ 'C:/vcpkg/installed/x64-windows/bin', 'C:/msys64/mingw64/bin' ]:
				if os.path.isdir(dll_dir):
					os.add_dll_directory(dll_dir)

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
