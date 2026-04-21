import ctypes

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
LOG_CB_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p)


def init_ctypes(rtc_library : ctypes.CDLL) -> None:
	rtc_library.rtcInitLogger.argtypes = [ ctypes.c_int, LOG_CB_TYPE ]
	rtc_library.rtcInitLogger.restype = None
	rtc_library.rtcInitLogger(4, LOG_CB_TYPE(0))

	rtc_library.rtcCreatePeerConnection.argtypes = [ ctypes.POINTER(RTC_CONFIGURATION) ]
	rtc_library.rtcCreatePeerConnection.restype = ctypes.c_int

	rtc_library.rtcDeletePeerConnection.argtypes = [ ctypes.c_int ]
	rtc_library.rtcDeletePeerConnection.restype = ctypes.c_int

	rtc_library.rtcSetRemoteDescription.argtypes = [ ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p ]
	rtc_library.rtcSetRemoteDescription.restype = ctypes.c_int

	rtc_library.rtcAddTrack.argtypes = [ ctypes.c_int, ctypes.c_char_p ]
	rtc_library.rtcAddTrack.restype = ctypes.c_int

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

	rtc_library.rtcChainRtcpNackResponder.argtypes = [ ctypes.c_int, ctypes.c_uint ]
	rtc_library.rtcChainRtcpNackResponder.restype = ctypes.c_int

	rtc_library.rtcGetLocalDescription.argtypes = [ ctypes.c_int, ctypes.c_char_p, ctypes.c_int ]
	rtc_library.rtcGetLocalDescription.restype = ctypes.c_int

	rtc_library.rtcSetOpusPacketizer.argtypes = [ ctypes.c_int, ctypes.POINTER(RTC_PACKETIZER_INIT) ]
	rtc_library.rtcSetOpusPacketizer.restype = ctypes.c_int

	return None
