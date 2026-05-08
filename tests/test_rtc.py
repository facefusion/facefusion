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


# TODO: enable again
@pytest.mark.skip
def test_create_peer_connection() -> None:
	peer_connection = rtc.create_peer_connection()
	datachannel_library = rtc.create_static_datachannel_library()

	assert peer_connection > 0
	assert datachannel_library.rtcDeletePeerConnection(peer_connection) == 0


# TODO: enable again
@pytest.mark.skip
def test_add_audio_track() -> None:
	peer_connection = rtc.create_peer_connection()

	assert rtc.add_audio_track(peer_connection, 'sendonly') > 0

	rtc.create_static_datachannel_library().rtcDeletePeerConnection(peer_connection)


# TODO: enable again
@pytest.mark.skip
def test_add_video_track() -> None:
	peer_connection = rtc.create_peer_connection()

	assert rtc.add_video_track(peer_connection, 'sendonly') > 0

	rtc.create_static_datachannel_library().rtcDeletePeerConnection(peer_connection)


# TODO: enable again
@pytest.mark.skip
def test_negotiate_sdp() -> None:
	datachannel_library = rtc.create_static_datachannel_library()

	sender_connection = rtc.create_peer_connection()
	rtc.add_video_track(sender_connection, 'sendonly')
	rtc.add_audio_track(sender_connection, 'sendonly')
	sdp_offer = rtc.create_sdp(sender_connection)

	receiver_connection = rtc.create_peer_connection()
	rtc.add_video_track(receiver_connection, 'recvonly')
	rtc.add_audio_track(receiver_connection, 'recvonly')
	sdp_answer = rtc.negotiate_sdp(receiver_connection, sdp_offer)

	assert sdp_answer
	assert 'm=video' in sdp_answer
	assert 'VP8/90000' in sdp_answer
	assert 'm=audio' in sdp_answer
	assert 'opus/48000/2' in sdp_answer

	assert datachannel_library.rtcDeletePeerConnection(sender_connection) == 0
	assert datachannel_library.rtcDeletePeerConnection(receiver_connection) == 0


# TODO: enable again
@pytest.mark.skip
def test_delete_peers() -> None:
	datachannel_library = rtc.create_static_datachannel_library()
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
