import ctypes
import time
from typing import List, Optional

from facefusion.datachannel import create_rtc_configuration, create_rtc_packetizer_init, create_static_download_set, create_static_rtc_library
from facefusion.download import conditional_download_hashes, conditional_download_sources
from facefusion.types import MediaDirection, PeerConnection, RtcAudioTrack, RtcPeer, RtcVideoTrack, SdpAnswer, SdpOffer


def pre_check() -> bool:
	download_set = create_static_download_set()

	if not conditional_download_hashes(download_set.get('hashes')):
		return False
	return conditional_download_sources(download_set.get('sources'))


def create_peer_connection(
	ice_servers : Optional[ctypes.Array[ctypes.c_char_p]] = None,
	ice_servers_count : int = 0, proxy_server : Optional[bytes] = None,
	bind_address : Optional[bytes] = None, certificate_type : int = 0,
	ice_transport_policy : int = 0,
	enable_ice_tcp : bool = False,
	enable_ice_udp_mux : bool = True,
	disable_auto_negotiation : bool = False,
	force_media_transport : bool = True,
	port_range_begin : int = 0,
	port_range_end : int = 0,
	max_packet_size : int = 0,
	max_message_size : int = 0) -> PeerConnection:

	rtc_library = create_static_rtc_library()
	rtc_configuration = create_rtc_configuration()

	rtc_configuration.iceServers = ice_servers
	rtc_configuration.iceServersCount = ice_servers_count
	rtc_configuration.proxyServer = proxy_server
	rtc_configuration.bindAddress = bind_address
	rtc_configuration.certificateType = certificate_type
	rtc_configuration.iceTransportPolicy = ice_transport_policy
	rtc_configuration.enableIceTcp = enable_ice_tcp
	rtc_configuration.enableIceUdpMux = enable_ice_udp_mux
	rtc_configuration.disableAutoNegotiation = disable_auto_negotiation
	rtc_configuration.forceMediaTransport = force_media_transport
	rtc_configuration.portRangeBegin = port_range_begin
	rtc_configuration.portRangeEnd = port_range_end
	rtc_configuration.mtu = max_packet_size
	rtc_configuration.maxMessageSize = max_message_size

	return rtc_library.rtcCreatePeerConnection(ctypes.byref(rtc_configuration))


def build_media_description(media_type : str, payload_type : int, rtp_codec : str, media_direction : MediaDirection, media_id : int) -> bytes:
	return '\r\n'.join(
	[
		'm=' + media_type + ' 9 UDP/TLS/RTP/SAVPF ' + str(payload_type),
		'a=rtpmap:' + str(payload_type) + ' ' + rtp_codec,
		'a=' + media_direction,
		'a=mid:' + str(media_id),
		'a=rtcp-mux',
		''
	]).encode()


def add_audio_track(peer_connection : PeerConnection, media_direction : MediaDirection) -> RtcAudioTrack:
	rtc_library = create_static_rtc_library()
	media_description = build_media_description('audio', 111, 'opus/48000/2', media_direction, 1)

	audio_track = rtc_library.rtcAddTrack(peer_connection, media_description)

	audio_packetizer = create_rtc_packetizer_init()
	audio_packetizer.ssrc = 43
	audio_packetizer.cname = b'audio'
	audio_packetizer.payloadType = 111
	audio_packetizer.clockRate = 48000

	rtc_library.rtcSetOpusPacketizer(audio_track, ctypes.byref(audio_packetizer))
	rtc_library.rtcChainRtcpSrReporter(audio_track)

	return audio_track


def add_video_track(peer_connection : PeerConnection, media_direction : MediaDirection) -> RtcVideoTrack:
	rtc_library = create_static_rtc_library()
	media_description = build_media_description('video', 96, 'VP8/90000', media_direction, 0)

	video_track = rtc_library.rtcAddTrack(peer_connection, media_description)

	video_packetizer = create_rtc_packetizer_init()
	video_packetizer.ssrc = 42
	video_packetizer.cname = b'video'
	video_packetizer.payloadType = 96
	video_packetizer.clockRate = 90000
	video_packetizer.maxFragmentSize = 1200

	rtc_library.rtcSetVP8Packetizer(video_track, ctypes.byref(video_packetizer))
	rtc_library.rtcChainRtcpSrReporter(video_track)
	rtc_library.rtcChainRtcpNackResponder(video_track, 512)

	return video_track


def create_sdp(peer_connection : PeerConnection) -> Optional[SdpOffer]:
	rtc_library = create_static_rtc_library()
	rtc_library.rtcSetLocalDescription(peer_connection, b'offer')
	buffer_size = 16384
	buffer_string = ctypes.create_string_buffer(buffer_size)

	if rtc_library.rtcGetLocalDescription(peer_connection, buffer_string, buffer_size) > 0:
		return buffer_string.value.decode()

	return None


def negotiate_sdp(peer_connection : PeerConnection, sdp_offer : SdpOffer) -> Optional[SdpAnswer]:
	rtc_library = create_static_rtc_library()
	rtc_library.rtcSetRemoteDescription(peer_connection, sdp_offer.encode(), b'offer')
	buffer_size = 16384
	buffer_string = ctypes.create_string_buffer(buffer_size)
	wait_limit = time.monotonic() + 5

	while time.monotonic() < wait_limit:
		if rtc_library.rtcGetLocalDescription(peer_connection, buffer_string, buffer_size) > 0:
			return buffer_string.value.decode()
		time.sleep(0.05)

	return None


def handle_whep_offer(peers : List[RtcPeer], sdp_offer : SdpOffer) -> Optional[SdpAnswer]:
	peer_connection = create_peer_connection()
	audio_track = add_audio_track(peer_connection, 'sendonly')
	video_track = add_video_track(peer_connection, 'sendonly')
	local_sdp = negotiate_sdp(peer_connection, sdp_offer)

	if local_sdp:
		rtc_peer : RtcPeer =\
		{
			'peer_connection': peer_connection,
			'video_track': video_track,
			'audio_track': audio_track
		}
		peers.append(rtc_peer)

	return local_sdp


def send_to_peers(peers : List[RtcPeer], data : bytes) -> None:
	rtc_library = create_static_rtc_library()

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


def delete_peers(peers : List[RtcPeer]) -> None:
	rtc_library = create_static_rtc_library()

	for rtc_peer in peers:
		peer_connection_id = rtc_peer.get('peer_connection')

		if peer_connection_id:
			rtc_library.rtcDeletePeerConnection(peer_connection_id)

	peers.clear()


def is_peer_connected(peers : List[RtcPeer]) -> bool:
	rtc_library = create_static_rtc_library()

	for rtc_peer in peers:
		video_track_id = rtc_peer.get('video_track')

		if video_track_id and rtc_library.rtcIsOpen(video_track_id):
			return True

	return False
