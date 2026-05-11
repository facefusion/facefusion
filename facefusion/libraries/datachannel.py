import ctypes
from functools import lru_cache
from typing import Optional

from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url_by_provider
from facefusion.filesystem import resolve_relative_path
from facefusion.types import LibrarySet


@lru_cache
def create_static_library_set() -> Optional[LibrarySet]:
	if is_linux():
		return\
		{
			'hashes':
			{
				'datachannel':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0-a', 'linux/libdatachannel.hash'),
					'path': resolve_relative_path('../.libraries/libdatachannel.hash')
				},
				'crypto':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0-a', 'linux/libcrypto.hash'),
					'path': resolve_relative_path('../.libraries/libcrypto.hash')
				},
				'ssl':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0-a', 'linux/libssl.hash'),
					'path': resolve_relative_path('../.libraries/libssl.hash')
				}
			},
			'sources':
			{
				'datachannel':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0-a', 'linux/libdatachannel.so'),
					'path': resolve_relative_path('../.libraries/libdatachannel.so')
				},
				'crypto':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0-a', 'linux/libcrypto.so'),
					'path': resolve_relative_path('../.libraries/libcrypto.so')
				},
				'ssl':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0-a', 'linux/libssl.so'),
					'path': resolve_relative_path('../.libraries/libssl.so')
				}
			}
		}
	if is_macos():
		return\
		{
			'hashes':
			{
				'datachannel':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0-a', 'macos/libdatachannel.hash'),
					'path': resolve_relative_path('../.libraries/libdatachannel.hash')
				},
				'crypto':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0-a', 'macos/libcrypto.hash'),
					'path': resolve_relative_path('../.libraries/libcrypto.hash')
				},
				'ssl':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0-a', 'macos/libssl.hash'),
					'path': resolve_relative_path('../.libraries/libssl.hash')
				}
			},
			'sources':
			{
				'datachannel':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0-a', 'macos/libdatachannel.dylib'),
					'path': resolve_relative_path('../.libraries/libdatachannel.dylib')
				},
				'crypto':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0-a', 'macos/libcrypto.dylib'),
					'path': resolve_relative_path('../.libraries/libcrypto.dylib')
				},
				'ssl':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0-a', 'macos/libssl.dylib'),
					'path': resolve_relative_path('../.libraries/libssl.dylib')
				}
			}
		}
	if is_windows():
		return\
		{
			'hashes':
			{
				'datachannel':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', 'windows/datachannel.hash'),
					'path': resolve_relative_path('../.libraries/datachannel.hash')
				}
			},
			'sources':
			{
				'datachannel':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', 'windows/datachannel.dll'),
					'path': resolve_relative_path('../.libraries/datachannel.dll')
				}
			}
		}

	return None


def pre_check() -> bool:
	library_hash_set = create_static_library_set().get('hashes')
	library_source_set = create_static_library_set().get('sources')

	return conditional_download_hashes(library_hash_set) and conditional_download_sources(library_source_set)


@lru_cache
def create_static_library() -> Optional[ctypes.CDLL]:
	datachannel_source_path = create_static_library_set().get('sources').get('datachannel').get('path')
	crypto_source_path = create_static_library_set().get('sources').get('crypto').get('path')
	ssl_source_path = create_static_library_set().get('sources').get('ssl').get('path')

	if datachannel_source_path:
		if crypto_source_path and ssl_source_path:
			ctypes.CDLL(crypto_source_path)
			ctypes.CDLL(ssl_source_path)

		if is_windows():
			library = ctypes.CDLL(datachannel_source_path, winmode = 0)
		else:
			library = ctypes.CDLL(datachannel_source_path)

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
