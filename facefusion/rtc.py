import ctypes
import time
from typing import List, Optional, Tuple

from facefusion.rtc_helper import create_static_download_set
from facefusion.types import RtcAudioTrack, RtcPeer, RtcVideoTrack


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


def init_ctypes(rtc_library : ctypes.CDLL) -> bool:
	if rtc_library:
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

		return True

	return False


def load_library() -> Optional[ctypes.CDLL]:
	binary_path = create_static_download_set().get('sources').get('datachannel').get('path')

	if binary_path:
		rtc_library = ctypes.CDLL(binary_path)
		if init_ctypes(rtc_library):
			return rtc_library

	return None


def create_peer_connection(rtc_library : ctypes.CDLL) -> int:
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
	return rtc_library.rtcCreatePeerConnection(ctypes.byref(config))


def add_media_tracks(rtc_library : ctypes.CDLL, peer_connection : int) -> Tuple[RtcVideoTrack, RtcAudioTrack]:
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
	rtc_library.rtcChainRtcpNackResponder(video_track, 512)

	audio_packetizer = RTC_PACKETIZER_INIT()
	audio_packetizer.ssrc = 43
	audio_packetizer.cname = b'audio'
	audio_packetizer.payloadType = 111
	audio_packetizer.clockRate = 48000
	rtc_library.rtcSetOpusPacketizer(audio_track, ctypes.byref(audio_packetizer))
	rtc_library.rtcChainRtcpSrReporter(audio_track)
	return video_track, audio_track


def negotiate_sdp(rtc_library : ctypes.CDLL, peer_connection : int, sdp_offer : str) -> Optional[str]:
	rtc_library.rtcSetRemoteDescription(peer_connection, sdp_offer.encode('utf-8'), b'offer')
	buffer_size = 16384
	buffer_string = ctypes.create_string_buffer(buffer_size)
	wait_limit = time.monotonic() + 5

	while time.monotonic() < wait_limit:
		if rtc_library.rtcGetLocalDescription(peer_connection, buffer_string, buffer_size) > 0:
			return buffer_string.value.decode()
		time.sleep(0.05)

	return None


def handle_whep_offer(rtc_library : ctypes.CDLL, peers : List[RtcPeer], sdp_offer : str) -> Optional[str]:
	peer_connection = create_peer_connection(rtc_library)
	video_track, audio_track = add_media_tracks(rtc_library, peer_connection)
	local_sdp = negotiate_sdp(rtc_library, peer_connection, sdp_offer)

	if local_sdp:
		rtc_peer : RtcPeer =\
		{
			'peer_connection': peer_connection,
			'video_track': video_track,
			'audio_track': audio_track
		}
		peers.append(rtc_peer)

	return local_sdp


def send_to_peers(rtc_library : ctypes.CDLL, peers : List[RtcPeer], data : bytes) -> None:
	if peers:
		timestamp = int(time.monotonic() * 90000) & 0xFFFFFFFF
		data_buffer = ctypes.create_string_buffer(data)
		data_total = len(data)

		for rtc_peer in peers:
			video_track_id = rtc_peer.get('video_track')

			if video_track_id and rtc_library.rtcIsOpen(video_track_id):
				rtc_library.rtcSetTrackRtpTimestamp(video_track_id, timestamp)
				rtc_library.rtcSendMessage(video_track_id, data_buffer, data_total)

	return None


def delete_peers(rtc_library : ctypes.CDLL, peers : List[RtcPeer]) -> None:
	for rtc_peer in peers:
		peer_connection_id = rtc_peer.get('peer_connection')

		if peer_connection_id:
			rtc_library.rtcDeletePeerConnection(peer_connection_id)

	peers.clear()
