import ctypes
import threading
from functools import partial
from time import sleep
from typing import List, Tuple

import pytest

from facefusion import rtc, state_manager
from facefusion.apis.stream_event import create_receive_event, destroy_receive_event, dispatch_event, dispatch_frame
from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import Buffer, PeerConnection, RtcPeer, RtcVideoTrack, Timestamp


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])

	datachannel_module.pre_check()


def collect_frame(frames : List[Tuple[Buffer, Timestamp]], frame_buffer : Buffer, frame_timestamp : Timestamp) -> None:
	frames.append((frame_buffer, frame_timestamp))


def create_video_loopback() -> Tuple[PeerConnection, RtcVideoTrack, PeerConnection, RtcVideoTrack]:
	datachannel_library = datachannel_module.create_static_library()
	sender_peer_connection = rtc.create_peer_connection()
	sender_track = rtc.add_video_track(sender_peer_connection, 'sendonly', 'vp8', 96)
	sdp_offer = rtc.create_sdp_offer(sender_peer_connection)

	rtc_configuration = datachannel_module.define_rtc_configuration()
	rtc_configuration.forceMediaTransport = True
	rtc_configuration.disableAutoNegotiation = True
	receiver_peer_connection = datachannel_library.rtcCreatePeerConnection(ctypes.byref(rtc_configuration))
	rtc.set_remote_description(receiver_peer_connection, sdp_offer)

	track_init = datachannel_module.define_rtc_track_init()
	track_init.direction = 2
	track_init.codec = 1
	track_init.payloadType = 96
	track_init.mid = '1'.encode()
	track_init.name = 'video'.encode()
	receiver_track = datachannel_library.rtcAddTrackEx(receiver_peer_connection, ctypes.byref(track_init))

	video_depacketizer = datachannel_module.define_rtc_packetizer_init()
	video_depacketizer.cname = 'video'.encode()
	video_depacketizer.payloadType = 96
	video_depacketizer.clockRate = 90000
	datachannel_library.rtcSetVP8Depacketizer(receiver_track, ctypes.byref(video_depacketizer))

	sdp_answer = rtc.create_sdp_answer(receiver_peer_connection)
	datachannel_library.rtcSetRemoteDescription(sender_peer_connection, sdp_answer.encode(), 'answer'.encode())
	return sender_peer_connection, sender_track, receiver_peer_connection, receiver_track


def create_rtc_peer(peer_connection : PeerConnection, sender_track : RtcVideoTrack) -> RtcPeer:
	rtc_peer : RtcPeer =\
	{
		'peer_connection': peer_connection,
		'video':
		{
			'sender_track': sender_track,
			'receiver_track': 0,
			'codec': 'vp8'
		},
		'sender_bitrate': ctypes.c_uint(0),
		'receiver_bitrate': ctypes.c_uint(0)
	}
	return rtc_peer


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


def test_create_receive_event() -> None:
	datachannel_library = datachannel_module.create_static_library()
	sender_peer_connection, sender_track, receiver_peer_connection, receiver_track = create_video_loopback()
	frames : List[Tuple[Buffer, Timestamp]] = []
	receive_event = create_receive_event(receiver_track, partial(collect_frame, frames))

	assert receive_event.is_set() is False
	assert wait_for_open(sender_track) is True

	rtc.send_video(create_rtc_peer(sender_peer_connection, sender_track), bytes([ 1 ] * 100), 3000)
	rtc.send_video(create_rtc_peer(sender_peer_connection, sender_track), bytes([ 2 ] * 200), 6000)

	assert wait_for_frames(frames, 2) == [ (bytes([ 1 ] * 100), 3000), (bytes([ 2 ] * 200), 6000) ]
	assert receive_event.is_set() is False

	datachannel_library.rtcDeletePeerConnection(receiver_peer_connection)

	assert receive_event.wait(5) is True

	datachannel_library.rtcDeletePeerConnection(sender_peer_connection)


def test_destroy_receive_event() -> None:
	datachannel_library = datachannel_module.create_static_library()
	sender_peer_connection, sender_track, receiver_peer_connection, receiver_track = create_video_loopback()
	frames : List[Tuple[Buffer, Timestamp]] = []
	receive_event = create_receive_event(receiver_track, partial(collect_frame, frames))

	assert wait_for_open(sender_track) is True

	destroy_receive_event(receiver_track)
	rtc.send_video(create_rtc_peer(sender_peer_connection, sender_track), bytes([ 1 ] * 100), 3000)
	sleep(0.5)

	assert frames == []

	datachannel_library.rtcDeletePeerConnection(receiver_peer_connection)

	assert receive_event.wait(1) is False

	datachannel_library.rtcDeletePeerConnection(sender_peer_connection)


def test_dispatch_frame() -> None:
	frames : List[Tuple[Buffer, Timestamp]] = []
	frame_buffer = ctypes.create_string_buffer(bytes([ 1, 2, 3 ]), 3)
	frame_info = ctypes.c_uint32(3000)

	dispatch_frame(partial(collect_frame, frames), 0, ctypes.cast(frame_buffer, ctypes.c_void_p), 3, ctypes.cast(ctypes.pointer(frame_info), ctypes.c_void_p), ctypes.c_void_p(0))

	assert frames == [ (bytes([ 1, 2, 3 ]), 3000) ]


def test_dispatch_event() -> None:
	receive_event = threading.Event()

	dispatch_event(receive_event, 0, ctypes.c_void_p(0))

	assert receive_event.is_set() is True
