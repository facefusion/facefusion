import ctypes
from functools import partial
from time import sleep
from typing import List, Tuple

import pytest

from facefusion import state_manager
from facefusion.apis.stream_event import create_receive_event
from facefusion.libraries import datachannel as datachannel_module, opus as opus_module, vpx as vpx_module
from facefusion.rtc import adapt_receiver_bitrate, add_audio_track, add_video_track, create_peer_connection, create_sdp_answer, create_sdp_offer, delete_peer, get_payload_type, handle_sender_bitrate, send_audio, send_video, set_remote_description, wire_sender_bitrate
from facefusion.types import Buffer, PeerConnection, RtcPeer, SdpOffer, Timestamp, VideoCodec


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])

	datachannel_module.pre_check()
	opus_module.pre_check()
	vpx_module.pre_check()


def collect_frame(frames : List[Tuple[Buffer, Timestamp]], frame_buffer : Buffer, frame_timestamp : Timestamp) -> None:
	frames.append((frame_buffer, frame_timestamp))


def create_receiver_peer_connection(sdp_offer : SdpOffer) -> PeerConnection:
	datachannel_library = datachannel_module.create_static_library()
	rtc_configuration = datachannel_module.define_rtc_configuration()
	rtc_configuration.forceMediaTransport = True
	rtc_configuration.disableAutoNegotiation = True
	receiver_peer_connection = datachannel_library.rtcCreatePeerConnection(ctypes.byref(rtc_configuration))
	set_remote_description(receiver_peer_connection, sdp_offer)
	return receiver_peer_connection


def add_receiver_video_track(peer_connection : PeerConnection) -> int:
	datachannel_library = datachannel_module.create_static_library()
	track_init = datachannel_module.define_rtc_track_init()
	track_init.direction = 2
	track_init.codec = 1
	track_init.payloadType = 96
	track_init.mid = '1'.encode()
	track_init.name = 'video'.encode()
	video_track = datachannel_library.rtcAddTrackEx(peer_connection, ctypes.byref(track_init))
	video_depacketizer = datachannel_module.define_rtc_packetizer_init()
	video_depacketizer.cname = 'video'.encode()
	video_depacketizer.payloadType = 96
	video_depacketizer.clockRate = 90000
	datachannel_library.rtcSetVP8Depacketizer(video_track, ctypes.byref(video_depacketizer))
	return video_track


def add_receiver_audio_track(peer_connection : PeerConnection) -> int:
	datachannel_library = datachannel_module.create_static_library()
	track_init = datachannel_module.define_rtc_track_init()
	track_init.direction = 2
	track_init.codec = 128
	track_init.payloadType = 111
	track_init.mid = '3'.encode()
	track_init.name = 'audio'.encode()
	audio_track = datachannel_library.rtcAddTrackEx(peer_connection, ctypes.byref(track_init))
	audio_depacketizer = datachannel_module.define_rtc_packetizer_init()
	audio_depacketizer.cname = 'audio'.encode()
	audio_depacketizer.payloadType = 111
	audio_depacketizer.clockRate = 48000
	datachannel_library.rtcSetOpusDepacketizer(audio_track, ctypes.byref(audio_depacketizer))
	return audio_track


def connect_peer_connection(sender_peer_connection : PeerConnection, receiver_peer_connection : PeerConnection) -> None:
	datachannel_library = datachannel_module.create_static_library()
	sdp_answer = create_sdp_answer(receiver_peer_connection)
	datachannel_library.rtcSetRemoteDescription(sender_peer_connection, sdp_answer.encode(), 'answer'.encode())


def wait_for_open(track : int) -> bool:
	datachannel_library = datachannel_module.create_static_library()

	for _ in range(50):
		if datachannel_library.rtcIsOpen(track) is False:
			sleep(0.1)

	return datachannel_library.rtcIsOpen(track)


def wait_for_frames(frames : List[Tuple[Buffer, Timestamp]], frame_total : int) -> List[Tuple[Buffer, Timestamp]]:
	for _ in range(50):
		if len(frames) < frame_total:
			sleep(0.1)

	return frames


def test_create_peer_connection() -> None:
	peer_connection = create_peer_connection()
	datachannel_library = datachannel_module.create_static_library()

	assert peer_connection
	assert datachannel_library.rtcDeletePeerConnection(peer_connection) == 0


def test_create_sdp_offer() -> None:
	sender_peer_connection = create_peer_connection()
	add_video_track(sender_peer_connection, 'sendonly', 'vp8', 96)
	add_audio_track(sender_peer_connection, 'sendonly', 'opus', 111)
	sdp_offer = create_sdp_offer(sender_peer_connection)

	assert 'm=video' in sdp_offer
	assert 'VP8/90000' in sdp_offer
	assert 'a=ssrc:42 cname:video' in sdp_offer
	assert 'm=audio' in sdp_offer
	assert 'opus/48000/2' in sdp_offer
	assert 'a=ssrc:43 cname:audio' in sdp_offer

	datachannel_module.create_static_library().rtcDeletePeerConnection(sender_peer_connection)


def test_create_sdp_answer() -> None:
	datachannel_library = datachannel_module.create_static_library()

	sender_peer_connection = create_peer_connection()
	add_video_track(sender_peer_connection, 'sendonly', 'vp8', 96)
	add_audio_track(sender_peer_connection, 'sendonly', 'opus', 111)
	sdp_offer = create_sdp_offer(sender_peer_connection)

	receiver_peer_connection = create_peer_connection()
	set_remote_description(receiver_peer_connection, sdp_offer)
	add_video_track(receiver_peer_connection, 'recvonly', 'vp8', 96)
	add_audio_track(receiver_peer_connection, 'recvonly', 'opus', 111)
	sdp_answer = create_sdp_answer(receiver_peer_connection)

	assert 'm=video' in sdp_answer
	assert 'VP8/90000' in sdp_answer
	assert 'm=audio' in sdp_answer
	assert 'opus/48000/2' in sdp_answer
	assert 'a=recvonly' in sdp_answer

	assert datachannel_library.rtcDeletePeerConnection(sender_peer_connection) == 0
	assert datachannel_library.rtcDeletePeerConnection(receiver_peer_connection) == 0


def test_send_video() -> None:
	datachannel_library = datachannel_module.create_static_library()
	sender_peer_connection = create_peer_connection()
	video_track = add_video_track(sender_peer_connection, 'sendonly', 'vp8', 96)
	rtc_peer : RtcPeer =\
	{
		'peer_connection': sender_peer_connection,
		'video':
		{
			'sender_track': video_track,
			'receiver_track': video_track,
			'codec': 'vp8'
		},
		'sender_bitrate': ctypes.c_uint(0),
		'receiver_bitrate': ctypes.c_uint(0)
	}
	receiver_peer_connection = create_receiver_peer_connection(create_sdp_offer(sender_peer_connection))
	frames : List[Tuple[Buffer, Timestamp]] = []
	create_receive_event(add_receiver_video_track(receiver_peer_connection), partial(collect_frame, frames))

	send_video(rtc_peer, bytes([ 1 ] * 1024), 0)
	connect_peer_connection(sender_peer_connection, receiver_peer_connection)

	assert wait_for_open(video_track) is True

	send_video(rtc_peer, bytes([ 2 ] * 1024), 3000)

	assert wait_for_frames(frames, 1) == [ (bytes([ 2 ] * 1024), 3000) ]

	datachannel_library.rtcDeletePeerConnection(receiver_peer_connection)
	datachannel_library.rtcDeletePeerConnection(sender_peer_connection)


def test_send_audio() -> None:
	datachannel_library = datachannel_module.create_static_library()
	sender_peer_connection = create_peer_connection()
	audio_track = add_audio_track(sender_peer_connection, 'sendonly', 'opus', 111)
	rtc_peer : RtcPeer =\
	{
		'peer_connection': sender_peer_connection,
		'video':
		{
			'sender_track': 0,
			'receiver_track': 0,
			'codec': 'vp8'
		},
		'audio':
		{
			'sender_track': audio_track,
			'receiver_track': audio_track,
			'codec': 'opus'
		},
		'sender_bitrate': ctypes.c_uint(0),
		'receiver_bitrate': ctypes.c_uint(0)
	}
	receiver_peer_connection = create_receiver_peer_connection(create_sdp_offer(sender_peer_connection))
	frames : List[Tuple[Buffer, Timestamp]] = []
	create_receive_event(add_receiver_audio_track(receiver_peer_connection), partial(collect_frame, frames))

	send_audio(rtc_peer, bytes([ 1 ] * 960), 0)
	connect_peer_connection(sender_peer_connection, receiver_peer_connection)

	assert wait_for_open(audio_track) is True

	send_audio(rtc_peer, bytes([ 2 ] * 960), 960)

	assert wait_for_frames(frames, 1) == [ (bytes([ 2 ] * 960), 960) ]

	datachannel_library.rtcDeletePeerConnection(receiver_peer_connection)
	datachannel_library.rtcDeletePeerConnection(sender_peer_connection)


def test_delete_peer() -> None:
	datachannel_library = datachannel_module.create_static_library()
	peer_connection = create_peer_connection()
	rtc_peer : RtcPeer =\
	{
		'peer_connection': peer_connection,
		'video':
		{
			'sender_track': 0,
			'receiver_track': 0,
			'codec': 'vp8'
		},
		'sender_bitrate': ctypes.c_uint(0),
		'receiver_bitrate': ctypes.c_uint(0)
	}

	delete_peer(rtc_peer)

	assert datachannel_library.rtcDeletePeerConnection(peer_connection) == -1


def test_get_payload_type() -> None:
	peer_connection = create_peer_connection()
	add_video_track(peer_connection, 'sendonly', 'vp8', 96)
	add_audio_track(peer_connection, 'sendonly', 'opus', 111)
	sdp_offer = create_sdp_offer(peer_connection)

	assert get_payload_type(sdp_offer, 'vp8') == 96
	assert get_payload_type(sdp_offer, 'opus') == 111
	assert get_payload_type(sdp_offer, 'av1') == 0

	datachannel_module.create_static_library().rtcDeletePeerConnection(peer_connection)


@pytest.mark.parametrize('video_codec, payload_type', [ ('av1', 35), ('vp8', 96) ])
def test_wire_sender_bitrate(video_codec : VideoCodec, payload_type : int) -> None:
	datachannel_library = datachannel_module.create_static_library()
	peer_connection = create_peer_connection()
	video_sender_track = add_video_track(peer_connection, 'sendonly', video_codec, payload_type)
	rtc_peer : RtcPeer =\
	{
		'peer_connection': peer_connection,
		'video':
		{
			'sender_track': video_sender_track,
			'receiver_track': video_sender_track,
			'codec': video_codec
		},
		'sender_bitrate': ctypes.c_uint(0),
		'receiver_bitrate': ctypes.c_uint(0)
	}

	wire_sender_bitrate(video_sender_track, rtc_peer.get('sender_bitrate'))

	assert rtc_peer.get('sender_bitrate').value == 0

	handle_sender_bitrate(0, 8000000, ctypes.addressof(rtc_peer.get('sender_bitrate')))

	assert rtc_peer.get('sender_bitrate').value == 8000

	datachannel_library.rtcDeletePeerConnection(peer_connection)


@pytest.mark.parametrize('video_codec, payload_type', [ ('av1', 35), ('vp8', 96) ])
def test_adapt_receiver_bitrate(video_codec : VideoCodec, payload_type : int) -> None:
	datachannel_library = datachannel_module.create_static_library()
	peer_connection = create_peer_connection()
	video_sender_track = add_video_track(peer_connection, 'sendonly', video_codec, payload_type)
	video_receiver_track = add_video_track(peer_connection, 'recvonly', video_codec, payload_type)
	rtc_peer : RtcPeer =\
	{
		'peer_connection': peer_connection,
		'video':
		{
			'sender_track': video_sender_track,
			'receiver_track': video_receiver_track,
			'codec': video_codec
		},
		'sender_bitrate': ctypes.c_uint(0),
		'receiver_bitrate': ctypes.c_uint(8000)
	}

	adapt_receiver_bitrate(rtc_peer, 4000)

	assert rtc_peer.get('receiver_bitrate').value == 4000

	datachannel_library.rtcDeletePeerConnection(peer_connection)
