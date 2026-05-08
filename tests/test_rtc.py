from typing import List

import pytest

from facefusion import rtc
from facefusion.types import RtcPeer


@pytest.fixture(scope = 'module')
def before_all() -> None:
	rtc.pre_check()


def test_build_media_description() -> None:
	assert rtc.build_media_description('audio', 111, 'opus/48000/2', 'sendonly', 1) == b'm=audio 9 UDP/TLS/RTP/SAVPF 111\r\na=rtpmap:111 opus/48000/2\r\na=sendonly\r\na=mid:1\r\na=rtcp-mux\r\n'
	assert rtc.build_media_description('video', 96, 'VP8/90000', 'recvonly', 0) == b'm=video 9 UDP/TLS/RTP/SAVPF 96\r\na=rtpmap:96 VP8/90000\r\na=recvonly\r\na=mid:0\r\na=rtcp-mux\r\n'


def test_create_peer_connection() -> None:
	peer_connection = rtc.create_peer_connection()
	datachannel_library = rtc.create_static_datachannel_library()

	assert peer_connection > 0
	assert datachannel_library.rtcDeletePeerConnection(peer_connection) == 0


def test_add_audio_track() -> None:
	datachannel_library = rtc.create_static_datachannel_library()

	sender_connection = rtc.create_peer_connection()
	sender_audio_track = rtc.add_audio_track(sender_connection, 'sendonly')
	sdp_offer = rtc.create_sdp(sender_connection)

	receiver_connection = rtc.create_peer_connection()
	receiver_audio_track = rtc.add_audio_track(receiver_connection, 'recvonly')
	sdp_answer = rtc.negotiate_sdp(receiver_connection, sdp_offer)

	assert sender_audio_track > 0
	assert receiver_audio_track > 0

	assert 'm=audio' in sdp_offer
	assert 'm=audio' in sdp_answer
	assert 'opus/48000/2' in sdp_offer
	assert 'opus/48000/2' in sdp_answer

	assert datachannel_library.rtcDeletePeerConnection(sender_connection) == 0
	assert datachannel_library.rtcDeletePeerConnection(receiver_connection) == 0


def test_add_video_track() -> None:
	datachannel_library = rtc.create_static_datachannel_library()

	sender_connection = rtc.create_peer_connection()
	sender_video_track = rtc.add_video_track(sender_connection, 'sendonly')
	sdp_offer = rtc.create_sdp(sender_connection)

	receiver_connection = rtc.create_peer_connection()
	receiver_video_track = rtc.add_video_track(receiver_connection, 'recvonly')
	sdp_answer = rtc.negotiate_sdp(receiver_connection, sdp_offer)

	assert sender_video_track > 0
	assert receiver_video_track > 0

	assert 'm=video' in sdp_offer
	assert 'm=video' in sdp_answer
	assert 'VP8/90000' in sdp_offer
	assert 'VP8/90000' in sdp_answer

	assert datachannel_library.rtcDeletePeerConnection(sender_connection) == 0
	assert datachannel_library.rtcDeletePeerConnection(receiver_connection) == 0


def test_has_connected_peer() -> None:
	connected_peer : RtcPeer =\
	{
		'peer_connection_id': 1,
		'video_track': 1,
		'audio_track': 1,
		'connected': True
	}
	disconnected_peer : RtcPeer =\
	{
		'peer_connection_id': 2,
		'video_track': 2,
		'audio_track': 2,
		'connected': False
	}

	assert rtc.has_connected_peer([ connected_peer ]) is True
	assert rtc.has_connected_peer([ disconnected_peer ]) is False
	assert rtc.has_connected_peer([]) is False
	assert rtc.has_connected_peer([ disconnected_peer, connected_peer ]) is True


def test_delete_peers(before_all : None) -> None:
	peer_connection = rtc.create_peer_connection()
	peers : List[RtcPeer] =\
	[{
		'peer_connection_id': peer_connection,
		'video_track': 0,
		'audio_track': 0,
		'connected': True
	}]

	rtc.delete_peers(peers)

	assert peers == []
