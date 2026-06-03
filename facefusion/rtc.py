import ctypes
from typing import List, Optional

from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import AudioCodec, BitRate, MediaDirection, PeerConnection, RtcAudioTrack, RtcPeer, RtcTrackInit, RtcVideoTrack, SdpAnswer, SdpOffer, VideoCodec


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

	if rtc_peer.get('video'):
		video_track = rtc_peer.get('video').get('sender_track')

		if datachannel_library.rtcIsOpen(video_track):
			video_total = len(video_buffer)
			datachannel_library.rtcSetTrackRtpTimestamp(video_track, video_timestamp)
			datachannel_library.rtcSendMessage(video_track, video_buffer, video_total)

	return None


def send_audio(rtc_peer : RtcPeer, audio_buffer : bytes, audio_timestamp : int) -> None:
	datachannel_library = datachannel_module.create_static_library()

	if rtc_peer.get('audio'):
		audio_track = rtc_peer.get('audio').get('sender_track')

		if datachannel_library.rtcIsOpen(audio_track):
			audio_total = len(audio_buffer)
			datachannel_library.rtcSetTrackRtpTimestamp(audio_track, audio_timestamp)
			datachannel_library.rtcSendMessage(audio_track, audio_buffer, audio_total)

	return None


def delete_peers(rtc_peers : List[RtcPeer]) -> None:
	datachannel_library = datachannel_module.create_static_library()

	for rtc_peer in rtc_peers:
		peer_connection = rtc_peer.get('peer_connection')

		if peer_connection:
			datachannel_library.rtcDeletePeerConnection(peer_connection)

	return None


def add_audio_track(peer_connection : PeerConnection, media_direction : MediaDirection, audio_codec : AudioCodec, payload_type : int) -> RtcAudioTrack:
	datachannel_library = datachannel_module.create_static_library()
	audio_track_init = create_audio_track_init(media_direction, audio_codec, payload_type)
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


def add_video_track(peer_connection : PeerConnection, media_direction : MediaDirection, video_codec : VideoCodec, payload_type : int) -> RtcVideoTrack:
	datachannel_library = datachannel_module.create_static_library()
	video_track_init = create_video_track_init(media_direction, video_codec, payload_type)
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


def create_audio_track_init(media_direction : MediaDirection, audio_codec : AudioCodec, payload_type : int) -> RtcTrackInit:
	track_init = datachannel_module.define_rtc_track_init()
	track_init.name = b'audio'
	track_init.payloadType = payload_type

	if media_direction == 'sendonly':
		track_init.direction = 1
		track_init.mid = b'3'
		track_init.ssrc = 43

	if media_direction == 'recvonly':
		track_init.direction = 2
		track_init.mid = b'2'
		track_init.ssrc = 45

	if media_direction == 'sendrecv':
		track_init.direction = 3
		track_init.mid = b'1'
		track_init.ssrc = 43

	if audio_codec == 'opus':
		track_init.codec = 128

	return ctypes.byref(track_init)


def create_video_track_init(media_direction : MediaDirection, video_codec : VideoCodec, payload_type : int) -> RtcTrackInit:
	track_init = datachannel_module.define_rtc_track_init()
	track_init.name = b'video'
	track_init.payloadType = payload_type

	if media_direction == 'sendonly':
		track_init.direction = 1
		track_init.mid = b'1'
		track_init.ssrc = 42

	if media_direction == 'recvonly':
		track_init.direction = 2
		track_init.mid = b'0'
		track_init.ssrc = 44

	if media_direction == 'sendrecv':
		track_init.direction = 3
		track_init.mid = b'0'
		track_init.ssrc = 42

	if video_codec == 'av1':
		track_init.codec = 4

	if video_codec == 'vp8':
		track_init.codec = 1

	return ctypes.byref(track_init)


def get_payload_type(sdp_offer : SdpOffer, codec : AudioCodec | VideoCodec) -> int:
	datachannel_library = datachannel_module.create_static_library()
	payload_type_buffer = (ctypes.c_int * 16)()
	payload_type_total = datachannel_library.rtcGetPayloadTypesForCodec(sdp_offer.encode(), codec.lower().encode(), payload_type_buffer, 16)

	if payload_type_total:
		return payload_type_buffer[0]

	return 0


@ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_uint, ctypes.c_void_p)
def handle_sender_bitrate(_ : int, bitrate : BitRate, pointer : int) -> None:
	ctypes.cast(pointer, ctypes.POINTER(ctypes.c_uint)).contents.value = bitrate // 1000


def wire_sender_bitrate(video_track : RtcVideoTrack, bitrate : ctypes.c_uint) -> None:
	datachannel_library = datachannel_module.create_static_library()
	datachannel_library.rtcSetUserPointer(video_track, ctypes.cast(ctypes.byref(bitrate), ctypes.c_void_p))
	datachannel_library.rtcChainRembHandler(video_track, handle_sender_bitrate)


def adapt_receiver_bitrate(rtc_peer : RtcPeer, bitrate : BitRate) -> None:
	datachannel_library = datachannel_module.create_static_library()
	receiver_track = rtc_peer.get('video').get('receiver_track')

	rtc_peer.get('receiver_bitrate').value = bitrate
	datachannel_library.rtcRequestBitrate(receiver_track, bitrate * 1000)


def clear_bitrate(rtc_peer : RtcPeer) -> None:
	rtc_peer.get('sender_bitrate').value = 0
	rtc_peer.get('receiver_bitrate').value = 0
