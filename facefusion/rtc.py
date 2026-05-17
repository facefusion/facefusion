import ctypes
from typing import List, Optional

from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import AudioCodec, MediaDirection, PeerConnection, RtcAudioTrack, RtcPeer, RtcTrackInit, RtcVideoTrack, SdpAnswer, SdpMedia, SdpOffer, VideoCodec


def create_peer_connection() -> PeerConnection:
	datachannel_library = datachannel_module.create_static_library()
	rtc_configuration = datachannel_module.define_rtc_configuration()

	rtc_configuration.enableIceUdpMux = True
	rtc_configuration.forceMediaTransport = True
	rtc_configuration.disableAutoNegotiation = True

	return datachannel_library.rtcCreatePeerConnection(ctypes.byref(rtc_configuration))


def create_sdp_offer(peer_connection : PeerConnection) -> Optional[SdpOffer]:
	datachannel_library = datachannel_module.create_static_library()
	datachannel_library.rtcSetLocalDescription(peer_connection, b'offer')

	sdp_buffer = ctypes.create_string_buffer(8192)

	if datachannel_library.rtcGetLocalDescription(peer_connection, sdp_buffer, 8192):
		return sdp_buffer.value.decode()

	return None


def create_sdp_answer(peer_connection : PeerConnection) -> Optional[SdpAnswer]:
	datachannel_library = datachannel_module.create_static_library()
	datachannel_library.rtcSetLocalDescription(peer_connection, b'answer')

	sdp_buffer = ctypes.create_string_buffer(8192)

	if datachannel_library.rtcGetLocalDescription(peer_connection, sdp_buffer, 8192):
		return sdp_buffer.value.decode()

	return None


def set_remote_description(peer_connection : PeerConnection, sdp_offer : SdpOffer) -> None:
	datachannel_library = datachannel_module.create_static_library()
	datachannel_library.rtcSetRemoteDescription(peer_connection, sdp_offer.encode(), b'offer')

	return None


def send_video(rtc_peer : RtcPeer, video_buffer : bytes, video_timestamp : int) -> None:
	datachannel_library = datachannel_module.create_static_library()
	video_track = rtc_peer.get('video').get('sender_track')

	if datachannel_library.rtcIsOpen(video_track):
		send_buffer = ctypes.create_string_buffer(video_buffer)
		send_total = len(video_buffer)
		datachannel_library.rtcSetTrackRtpTimestamp(video_track, video_timestamp)
		datachannel_library.rtcSendMessage(video_track, send_buffer, send_total)

	return None


def send_audio(rtc_peer : RtcPeer, audio_buffer : bytes, audio_timestamp : int) -> None:
	datachannel_library = datachannel_module.create_static_library()
	audio = rtc_peer.get('audio')

	if audio:
		audio_track = audio.get('sender_track')

		if datachannel_library.rtcIsOpen(audio_track):
			send_buffer = ctypes.create_string_buffer(audio_buffer)
			send_total = len(audio_buffer)
			datachannel_library.rtcSetTrackRtpTimestamp(audio_track, audio_timestamp)
			datachannel_library.rtcSendMessage(audio_track, send_buffer, send_total)

	return None


def delete_peers(rtc_peers : List[RtcPeer]) -> None:
	datachannel_library = datachannel_module.create_static_library()

	for rtc_peer in rtc_peers:
		peer_connection = rtc_peer.get('peer_connection')

		if peer_connection:
			datachannel_library.rtcDeletePeerConnection(peer_connection)

	return None


def add_audio_track(peer_connection : PeerConnection, media_direction : MediaDirection, audio_codec : AudioCodec, payload_type : int, mid : bytes = b'1', ssrc : int = 43) -> RtcAudioTrack:
	datachannel_library = datachannel_module.create_static_library()
	audio_track_init = create_audio_track_init(media_direction, audio_codec, payload_type, mid, ssrc)
	audio_track = datachannel_library.rtcAddTrackEx(peer_connection, audio_track_init)

	if media_direction == 'sendonly':
		audio_packetizer = datachannel_module.define_rtc_packetizer_init()
		audio_packetizer.ssrc = 43
		audio_packetizer.cname = b'audio'
		audio_packetizer.payloadType = payload_type
		audio_packetizer.clockRate = 48000

		if audio_codec == 'opus':
			datachannel_library.rtcSetOpusPacketizer(audio_track, ctypes.byref(audio_packetizer))

		datachannel_library.rtcChainRtcpSrReporter(audio_track)

	if media_direction == 'recvonly':
		audio_depacketizer = datachannel_module.define_rtc_packetizer_init()
		audio_depacketizer.ssrc = 0
		audio_depacketizer.cname = b'audio'
		audio_depacketizer.payloadType = payload_type
		audio_depacketizer.clockRate = 48000

		if audio_codec == 'opus':
			datachannel_library.rtcSetOpusDepacketizer(audio_track, ctypes.byref(audio_depacketizer))

		datachannel_library.rtcChainRtcpReceivingSession(audio_track)

	return audio_track


def add_video_track(peer_connection : PeerConnection, media_direction : MediaDirection, video_codec : VideoCodec, payload_type : int, mid : bytes = b'0', ssrc : int = 42) -> RtcVideoTrack:
	datachannel_library = datachannel_module.create_static_library()
	video_track_init = create_video_track_init(media_direction, video_codec, payload_type, mid, ssrc)
	video_track = datachannel_library.rtcAddTrackEx(peer_connection, video_track_init)

	if media_direction == 'sendonly':
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

	if media_direction == 'recvonly':
		if video_codec == 'av1':
			datachannel_library.rtcSetAV1Depacketizer(video_track, 1)

		if video_codec == 'vp8':
			video_depacketizer = datachannel_module.define_rtc_packetizer_init()
			video_depacketizer.ssrc = 0
			video_depacketizer.cname = b'video'
			video_depacketizer.payloadType = payload_type
			video_depacketizer.clockRate = 90000
			datachannel_library.rtcSetVP8Depacketizer(video_track, ctypes.byref(video_depacketizer))

		datachannel_library.rtcChainRtcpReceivingSession(video_track)

	return video_track


def create_audio_track_init(media_direction : MediaDirection, audio_codec : AudioCodec, payload_type : int, mid : bytes, ssrc : int = 43) -> RtcTrackInit:
	track_init = datachannel_module.define_rtc_track_init()

	if media_direction == 'sendonly':
		track_init.direction = 1
	if media_direction == 'recvonly':
		track_init.direction = 2
	if media_direction == 'sendrecv':
		track_init.direction = 3
	if audio_codec == 'opus':
		track_init.codec = 128

	track_init.payloadType = payload_type
	track_init.ssrc = ssrc
	track_init.name = b'audio'
	track_init.mid = mid

	return ctypes.byref(track_init)


def create_video_track_init(media_direction : MediaDirection, video_codec : VideoCodec, payload_type : int, mid : bytes, ssrc : int = 42) -> RtcTrackInit:
	track_init = datachannel_module.define_rtc_track_init()

	if media_direction == 'sendonly':
		track_init.direction = 1
	if media_direction == 'recvonly':
		track_init.direction = 2
	if media_direction == 'sendrecv':
		track_init.direction = 3
	if video_codec == 'av1':
		track_init.codec = 4
	if video_codec == 'vp8':
		track_init.codec = 1

	track_init.payloadType = payload_type
	track_init.ssrc = ssrc
	track_init.name = b'video'
	track_init.mid = mid

	return ctypes.byref(track_init)


def detect_sdp_media(sdp_offer : SdpOffer) -> SdpMedia:
	sdp_media : SdpMedia = {}

	for line in sdp_offer.splitlines():
		if line.startswith('a=rtpmap:'):
			if 'av1/90000' in line.lower():
				sdp_media['video'] =\
				{
					'codec': 'av1',
					'payload_type': int(line.removeprefix('a=rtpmap:').split()[0])
				}
			if 'vp8/90000' in line.lower():
				sdp_media['video'] =\
				{
					'codec': 'vp8',
					'payload_type': int(line.removeprefix('a=rtpmap:').split()[0])
				}
			if 'opus/48000/2' in line.lower():
				sdp_media['audio'] =\
				{
					'codec': 'opus',
					'payload_type': int(line.removeprefix('a=rtpmap:').split()[0])
				}

	return sdp_media
