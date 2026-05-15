from typing import List

import pytest

from facefusion import rtc, state_manager
from facefusion.libraries import datachannel as datachannel_module, opus as opus_module, vpx as vpx_module
from facefusion.types import RtcPeer


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])

	datachannel_module.pre_check()
	opus_module.pre_check()
	vpx_module.pre_check()


def test_create_peer_connection() -> None:
	peer_connection = rtc.create_peer_connection()
	datachannel_library = datachannel_module.create_static_library()

	assert peer_connection > 0
	assert datachannel_library.rtcDeletePeerConnection(peer_connection) == 0


def test_create_sdp_offer() -> None:
	peer_connection = rtc.create_peer_connection()
	rtc.add_video_track(peer_connection, 'sendonly', 'vp8', 96)
	rtc.add_audio_track(peer_connection, 'sendonly', 'opus', 111)
	sdp_offer = rtc.create_sdp_offer(peer_connection)

	assert 'm=video' in sdp_offer
	assert 'VP8/90000' in sdp_offer
	assert 'a=ssrc:42 cname:video' in sdp_offer
	assert 'm=audio' in sdp_offer
	assert 'opus/48000/2' in sdp_offer
	assert 'a=ssrc:43 cname:audio' in sdp_offer

	datachannel_module.create_static_library().rtcDeletePeerConnection(peer_connection)


def test_negotiate_sdp_answer() -> None:
	datachannel_library = datachannel_module.create_static_library()

	sender_connection = rtc.create_peer_connection()
	rtc.add_video_track(sender_connection, 'sendonly', 'vp8', 96)
	rtc.add_audio_track(sender_connection, 'sendonly', 'opus', 111)
	sdp_offer = rtc.create_sdp_offer(sender_connection)

	receiver_connection = rtc.create_peer_connection()
	rtc.add_video_track(receiver_connection, 'recvonly', 'vp8', 96)
	rtc.add_audio_track(receiver_connection, 'recvonly', 'opus', 111)
	sdp_answer = rtc.negotiate_sdp_answer(receiver_connection, sdp_offer)

	assert 'm=video' in sdp_answer
	assert 'VP8/90000' in sdp_answer
	assert 'a=ssrc:42 cname:video' in sdp_answer
	assert 'm=audio' in sdp_answer
	assert 'opus/48000/2' in sdp_answer
	assert 'a=ssrc:43 cname:audio' in sdp_answer
	assert 'a=recvonly' in sdp_answer

	assert datachannel_library.rtcDeletePeerConnection(sender_connection) == 0
	assert datachannel_library.rtcDeletePeerConnection(receiver_connection) == 0


# TODO: review
def test_send_audio_to_peers() -> None:
	datachannel_library = datachannel_module.create_static_library()
	peer_connection = rtc.create_peer_connection()
	audio_track = rtc.add_audio_track(peer_connection, 'sendonly', 'opus', 111)
	rtc_peers : List[RtcPeer] =\
	[
		{
			'peer_connection': peer_connection,
			'video_track': 0,
			'audio_track': audio_track
		}
	]

	rtc.send_audio_to_peers(rtc_peers, bytes(960), 0)

	datachannel_library.rtcDeletePeerConnection(peer_connection)


# TODO: review
def test_send_video_to_peers() -> None:
	datachannel_library = datachannel_module.create_static_library()
	peer_connection = rtc.create_peer_connection()
	video_track = rtc.add_video_track(peer_connection, 'sendonly', 'vp8', 96)
	rtc_peers : List[RtcPeer] =\
	[
		{
			'peer_connection': peer_connection,
			'video_track': video_track,
			'audio_track': 0
		}
	]

	rtc.send_video_to_peers(rtc_peers, bytes(1024))

	datachannel_library.rtcDeletePeerConnection(peer_connection)


def test_delete_peers() -> None:
	datachannel_library = datachannel_module.create_static_library()
	peer_connection = rtc.create_peer_connection()
	rtc_peers : List[RtcPeer] =\
	[
		{
			'peer_connection': peer_connection,
			'video_track': 0,
			'audio_track': 0
		}
	]

	rtc.delete_peers(rtc_peers)

	assert datachannel_library.rtcDeletePeerConnection(peer_connection) < 0


def test_add_audio_track() -> None:
	peer_connection = rtc.create_peer_connection()
	audio_track = rtc.add_audio_track(peer_connection, 'sendonly', 'opus', 111)

	assert audio_track > 0

	# TODO: review
	sdp_offer = rtc.create_sdp_offer(peer_connection)

	assert 'opus/48000/2' in sdp_offer

	datachannel_module.create_static_library().rtcDeletePeerConnection(peer_connection)


def test_add_video_track() -> None:
	peer_connection = rtc.create_peer_connection()
	video_track = rtc.add_video_track(peer_connection, 'sendonly', 'vp8', 96)

	assert video_track > 0

	# TODO: review
	sdp_offer = rtc.create_sdp_offer(peer_connection)

	assert 'VP8/90000' in sdp_offer

	datachannel_module.create_static_library().rtcDeletePeerConnection(peer_connection)


