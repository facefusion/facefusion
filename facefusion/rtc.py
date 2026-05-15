import ctypes
import time
from typing import Dict, List, Optional

from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import AudioCodec, MediaDirection, PeerConnection, RtcAudioTrack, RtcPeer, RtcVideoTrack, SdpAnswer, SdpOffer, VideoCodec


def create_peer_connection() -> PeerConnection:
	datachannel_library = datachannel_module.create_static_library()
	rtc_configuration = datachannel_module.define_rtc_configuration()

	rtc_configuration.enableIceUdpMux = True
	rtc_configuration.forceMediaTransport = True

	return datachannel_library.rtcCreatePeerConnection(ctypes.byref(rtc_configuration))


def create_sdp_offer(peer_connection : PeerConnection) -> Optional[SdpOffer]:
	datachannel_library = datachannel_module.create_static_library()
	datachannel_library.rtcSetLocalDescription(peer_connection, b'offer')

	sdp_buffer = ctypes.create_string_buffer(8192)

	if datachannel_library.rtcGetLocalDescription(peer_connection, sdp_buffer, 8192):
		return sdp_buffer.value.decode()

	return None


def negotiate_sdp_answer(peer_connection : PeerConnection, sdp_offer : SdpOffer) -> Optional[SdpAnswer]:
	datachannel_library = datachannel_module.create_static_library()
	datachannel_library.rtcSetRemoteDescription(peer_connection, sdp_offer.encode(), b'offer')

	sdp_buffer = ctypes.create_string_buffer(8192)

	if datachannel_library.rtcGetLocalDescription(peer_connection, sdp_buffer, 8192):
		return sdp_buffer.value.decode()

	return None


#TODO: needs revision
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


#TODO: needs revision
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
	audio_track_init = create_audio_track_init(media_direction, audio_codec, payload_type)
	audio_track = datachannel_library.rtcAddTrackEx(peer_connection, audio_track_init)

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
	video_track_init = create_video_track_init(media_direction, video_codec, payload_type)
	video_track = datachannel_library.rtcAddTrackEx(peer_connection, video_track_init)

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


def create_audio_track_init(media_direction : MediaDirection, audio_codec : AudioCodec, payload_type : int) -> ctypes._CArgObject:
	track_init = datachannel_module.define_rtc_track_init()

	if media_direction == 'sendonly':
		track_init.direction = 1
	if media_direction == 'recvonly':
		track_init.direction = 2
	if audio_codec == 'opus':
		track_init.codec = 128

	track_init.payloadType = payload_type
	track_init.ssrc = 43
	track_init.name = b'audio'
	track_init.mid = b'1'

	return ctypes.byref(track_init)


def create_video_track_init(media_direction : MediaDirection, video_codec : VideoCodec, payload_type : int) -> ctypes._CArgObject:
	track_init = datachannel_module.define_rtc_track_init()

	if media_direction == 'sendonly':
		track_init.direction = 1
	if media_direction == 'recvonly':
		track_init.direction = 2
	if video_codec == 'av1':
		track_init.codec = 4
	if video_codec == 'vp8':
		track_init.codec = 1

	track_init.payloadType = payload_type
	track_init.ssrc = 42
	track_init.name = b'video'
	track_init.mid = b'0'

	return ctypes.byref(track_init)


#TODO: needs revision
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
