import ctypes
import threading
import time
from typing import Dict, List, Optional

from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import AudioCodec, MediaDirection, PeerConnection, RtcAudioTrack, RtcPeer, RtcVideoTrack, SdpAnswer, SdpOffer, VideoCodec


# TODO: reduce to only used params
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

	datachannel_library = datachannel_module.create_static_library()
	rtc_configuration = datachannel_module.define_rtc_configuration()

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

	return datachannel_library.rtcCreatePeerConnection(ctypes.byref(rtc_configuration))


# TODO: check if sleep is needed
def create_sdp_offer(peer_connection : PeerConnection) -> Optional[SdpOffer]:
	datachannel_library = datachannel_module.create_static_library()
	datachannel_library.rtcSetLocalDescription(peer_connection, b'offer')

	buffer_size = 16384
	buffer_string = ctypes.create_string_buffer(buffer_size)
	wait_limit = time.monotonic() + 5

	while time.monotonic() < wait_limit:
		if datachannel_library.rtcGetLocalDescription(peer_connection, buffer_string, buffer_size) > 0:
			return buffer_string.value.decode()

		time.sleep(0.05)

	return None


# TODO: sanitize sdp_offer, wrap in run_in_executor, track peer connection state
def negotiate_sdp_answer(peer_connection : PeerConnection, sdp_offer : SdpOffer) -> Optional[SdpAnswer]:
	datachannel_library = datachannel_module.create_static_library()
	sdp_event = threading.Event()
	sdp_event_pointer = ctypes.cast(id(sdp_event), ctypes.c_void_p)

	datachannel_library.rtcSetUserPointer(peer_connection, sdp_event_pointer)
	datachannel_library.rtcSetLocalDescriptionCallback(peer_connection, on_sdp_ready)
	datachannel_library.rtcSetRemoteDescription(peer_connection, sdp_offer.encode(), b'offer')
	sdp_event.wait(timeout = 5)

	sdp_buffer_size = 8192
	sdp_buffer = ctypes.create_string_buffer(sdp_buffer_size)

	if datachannel_library.rtcGetLocalDescription(peer_connection, sdp_buffer, sdp_buffer_size) > 0:
		return sdp_buffer.value.decode()

	return None


def send_audio_to_peers(rtc_peers : List[RtcPeer], audio_buffer : bytes, audio_pts : int) -> None:
	datachannel_library = datachannel_module.create_static_library()

	if rtc_peers:
		timestamp = audio_pts & 0xFFFFFFFF
		send_buffer = ctypes.create_string_buffer(audio_buffer)
		send_total = len(audio_buffer)

		for rtc_peer in rtc_peers:
			audio_track_id = rtc_peer.get('audio_track')

			if audio_track_id and datachannel_library.rtcIsOpen(audio_track_id):
				datachannel_library.rtcSetTrackRtpTimestamp(audio_track_id, timestamp)
				datachannel_library.rtcSendMessage(audio_track_id, send_buffer, send_total)

	return None


def send_video_to_peers(rtc_peers : List[RtcPeer], frame_buffer : bytes) -> None:
	datachannel_library = datachannel_module.create_static_library()

	if rtc_peers:
		timestamp = int(time.monotonic() * 90000) & 0xFFFFFFFF
		send_buffer = ctypes.create_string_buffer(frame_buffer)
		send_total = len(frame_buffer)

		for rtc_peer in rtc_peers:
			video_track_id = rtc_peer.get('video_track')

			if video_track_id and datachannel_library.rtcIsOpen(video_track_id):
				datachannel_library.rtcSetTrackRtpTimestamp(video_track_id, timestamp)
				datachannel_library.rtcSendMessage(video_track_id, send_buffer, send_total)

	return None


def delete_peers(rtc_peers : List[RtcPeer]) -> None:
	datachannel_library = datachannel_module.create_static_library()

	for rtc_peer in rtc_peers:
		peer_connection_id = rtc_peer.get('peer_connection')

		if peer_connection_id:
			datachannel_library.rtcDeletePeerConnection(peer_connection_id)

	return None


def add_audio_track(peer_connection : PeerConnection, media_direction : MediaDirection, audio_codec : AudioCodec, payload_type : int) -> RtcAudioTrack:
	datachannel_library = datachannel_module.create_static_library()
	media_description = create_audio_description(media_direction, audio_codec, payload_type)

	audio_track = datachannel_library.rtcAddTrack(peer_connection, media_description)

	audio_packetizer = datachannel_module.define_rtc_packetizer_init()
	audio_packetizer.ssrc = 43
	audio_packetizer.cname = b'audio'
	audio_packetizer.payloadType = payload_type
	audio_packetizer.clockRate = 48000

	if audio_codec == 'opus':
		datachannel_library.rtcSetOpusPacketizer(audio_track, ctypes.byref(audio_packetizer))

	datachannel_library.rtcChainRtcpSrReporter(audio_track)

	return audio_track


def add_video_track(peer_connection : PeerConnection, media_direction : MediaDirection, video_codec : VideoCodec, payload_type : int) -> RtcVideoTrack:
	datachannel_library = datachannel_module.create_static_library()
	media_description = create_video_description(media_direction, video_codec, payload_type)

	video_track = datachannel_library.rtcAddTrack(peer_connection, media_description)

	video_packetizer = datachannel_module.define_rtc_packetizer_init()
	video_packetizer.ssrc = 42
	video_packetizer.cname = b'video'
	video_packetizer.payloadType = payload_type
	video_packetizer.clockRate = 90000
	video_packetizer.maxFragmentSize = 1200

	if video_codec == 'av1':
		video_packetizer.obuPacketization = 1
		datachannel_library.rtcSetAV1Packetizer(video_track, ctypes.byref(video_packetizer))
	if video_codec == 'vp8':
		datachannel_library.rtcSetVP8Packetizer(video_track, ctypes.byref(video_packetizer))

	datachannel_library.rtcChainRtcpSrReporter(video_track)
	datachannel_library.rtcChainRtcpNackResponder(video_track, 512)

	return video_track


def create_audio_description(media_direction : MediaDirection, audio_codec : AudioCodec, payload_type : int) -> bytes:
	rtp_codec = 'opus/48000/2'
	if audio_codec == 'opus':
		rtp_codec = 'opus/48000/2'

	lines =\
	[
		'm=audio 9 UDP/TLS/RTP/SAVPF ' + str(payload_type),
		'a=rtpmap:' + str(payload_type) + ' ' + rtp_codec,
		'a=rtcp-fb:' + str(payload_type) + ' nack',
		'a=rtcp-fb:' + str(payload_type) + ' nack pli',
		'a=' + media_direction,
		'a=mid:1',
		'a=rtcp-mux',
		''
	]
	return '\r\n'.join(lines).encode()


def create_video_description(media_direction : MediaDirection, video_codec : VideoCodec, payload_type : int) -> bytes:
	rtp_codec = 'AV1/90000'
	if video_codec == 'av1':
		rtp_codec = 'AV1/90000'
	if video_codec == 'vp8':
		rtp_codec = 'VP8/90000'

	lines =\
	[
		'm=video 9 UDP/TLS/RTP/SAVPF ' + str(payload_type),
		'a=rtpmap:' + str(payload_type) + ' ' + rtp_codec,
		'a=rtcp-fb:' + str(payload_type) + ' nack',
		'a=rtcp-fb:' + str(payload_type) + ' nack pli',
		'a=' + media_direction,
		'a=mid:0',
		'a=rtcp-mux',
		''
	]
	return '\r\n'.join(lines).encode()


def parse_sdp_payload_types(sdp_offer : SdpOffer) -> Dict[str, int]:
	payload_types : Dict[str, int] = {}

	# TODO: consider having a codec helper to resolve these
	for line in sdp_offer.splitlines():
		if line.startswith('a=rtpmap:') and 'AV1/90000' in line and not payload_types.get('av1'):
			payload_types['av1'] = int(line.split(':')[1].split(' ')[0])
		if line.startswith('a=rtpmap:') and 'VP8/90000' in line and not payload_types.get('vp8'):
			payload_types['vp8'] = int(line.split(':')[1].split(' ')[0])
		if line.startswith('a=rtpmap:') and 'opus/48000/2' in line and not payload_types.get('opus'):
			payload_types['opus'] = int(line.split(':')[1].split(' ')[0])

	return payload_types


@ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
def on_sdp_ready(peer_connection : int, sdp : Optional[bytes], sdp_type : int, user_pointer : Optional[int]) -> None:
	ctypes.cast(user_pointer, ctypes.py_object).value.set()


# TODO: unused callback, remove or wire up
@ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)
def on_ice_complete(peer_connection : int, state : int, user_pointer : Optional[int]) -> None:
	if state == 2:
		context = ctypes.cast(user_pointer, ctypes.py_object).value
		context['event'].set()
