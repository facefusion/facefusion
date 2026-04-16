import ctypes
import threading
import time
from typing import Optional, Tuple

from facefusion.rtc_helper import RTC_CONFIGURATION, RTC_PACKETIZER_INIT, RTC_STATE, create_static_download_set, prepare_types
from facefusion.types import RtcAudioTrack, RtcPeer, RtcVideoTrack


def load_library() -> bool:
	binary_path = create_static_download_set().get('sources').get('datachannel').get('path')

	if binary_path:
		RTC_STATE['library'] = ctypes.CDLL(binary_path)
		prepare_types()
		return True

	return False


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
	return RTC_STATE.get('library').rtcCreatePeerConnection(ctypes.byref(config))


def create_rtc_session(stream_path : str) -> None:
	if stream_path not in RTC_STATE.get('sessions'):
		RTC_STATE.get('sessions')[stream_path] =\
		{
			'peers': []
		}


def destroy_rtc_session(stream_path : str) -> None:
	session = RTC_STATE.get('sessions').pop(stream_path, None)
	rtc_library = RTC_STATE.get('library')

	if session:
		for rtc_peer in session.get('peers'):
			peer_connection_id = rtc_peer.get('pc')

			if peer_connection_id is not None:
				rtc_library.rtcDeletePeerConnection(peer_connection_id)


def send_to_peers(stream_path : str, data : bytes) -> None:
	session = RTC_STATE.get('sessions').get(stream_path)

	if session:
		peers = session.get('peers')

		if peers:
			if RTC_STATE.get('send_start_time') == 0:
				RTC_STATE['send_start_time'] = time.monotonic()

			timestamp = int((time.monotonic() - RTC_STATE.get('send_start_time')) * 90000) & 0xFFFFFFFF
			data_buffer = ctypes.create_string_buffer(data)
			data_total = len(data)

			for rtc_peer in peers:
				if rtc_peer.get('connection'):
					video_track_id = rtc_peer.get('video_track')

					if video_track_id and RTC_STATE.get('library').rtcIsOpen(video_track_id):
						RTC_STATE.get('library').rtcSetTrackRtpTimestamp(video_track_id, timestamp)
						RTC_STATE.get('library').rtcSendMessage(video_track_id, data_buffer, data_total)

	return None


def register_pending_connection(peer_connection : int) -> threading.Event:
	ice_gather = threading.Event()
	rtc_library = RTC_STATE.get('library')

	RTC_STATE['pending_connections'][peer_connection] =\
	{
		'ice_gather': ice_gather,
		'local_sdp': None
	}

	rtc_library.rtcSetLocalDescriptionCallback(peer_connection, RTC_STATE.get('description_callback'))
	rtc_library.rtcSetGatheringStateChangeCallback(peer_connection, RTC_STATE.get('gathering_callback'))
	rtc_library.rtcSetStateChangeCallback(peer_connection, RTC_STATE.get('state_callback'))
	return ice_gather


def add_media_tracks(peer_connection : int) -> Tuple[RtcVideoTrack, RtcAudioTrack]:
	rtc_library = RTC_STATE.get('library')

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
	rtc_library.rtcSetOpenCallback(video_track, RTC_STATE.get('track_open_callback'))
	rtc_library.rtcChainRtcpNackResponder(video_track, 512)

	audio_packetizer = RTC_PACKETIZER_INIT()
	audio_packetizer.ssrc = 43
	audio_packetizer.cname = b'audio'
	audio_packetizer.payloadType = 111
	audio_packetizer.clockRate = 48000
	rtc_library.rtcSetOpusPacketizer(audio_track, ctypes.byref(audio_packetizer))
	rtc_library.rtcChainRtcpSrReporter(audio_track)
	return video_track, audio_track


def negotiate_sdp(peer_connection : int, sdp_offer : str, ice_gather : threading.Event) -> Optional[str]:
	RTC_STATE.get('library').rtcSetRemoteDescription(peer_connection, sdp_offer.encode('utf-8'), b'offer')
	ice_gather.wait(timeout = 5)
	pending_connection = RTC_STATE.get('pending_connections').pop(peer_connection, {})
	buffer_size = 16384
	buffer_string = ctypes.create_string_buffer(buffer_size)

	if RTC_STATE.get('library').rtcGetLocalDescription(peer_connection, buffer_string, buffer_size) > 0:
		return buffer_string.value.decode('utf-8')

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


def is_peer_connected(stream_path : str) -> bool:
	session = RTC_STATE.get('sessions').get(stream_path)

	if session:
		for rtc_peer in session.get('peers', []):
			if rtc_peer.get('connection'):
				return True

	return False


def start() -> None:
	load_library()


def stop() -> None:
	for stream_path in list(RTC_STATE.get('sessions').keys()):
		destroy_rtc_session(stream_path)
