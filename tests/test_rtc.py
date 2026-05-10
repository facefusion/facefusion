from typing import List

import pytest

from facefusion import environment, rtc, state_manager
from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import RtcPeer


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	environment.setup_for_system()
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])
	datachannel_module.pre_check()


# TODO: add test_parse_sdp_payload_types
def test_build_media_description() -> None:
	assert rtc.build_media_description('audio', 111, 'opus/48000/2', 'sendonly', 1) == b'm=audio 9 UDP/TLS/RTP/SAVPF 111\r\na=rtpmap:111 opus/48000/2\r\na=rtcp-fb:111 nack\r\na=rtcp-fb:111 nack pli\r\na=sendonly\r\na=mid:1\r\na=rtcp-mux\r\n'
	assert rtc.build_media_description('video', 96, 'VP8/90000', 'recvonly', 0) == b'm=video 9 UDP/TLS/RTP/SAVPF 96\r\na=rtpmap:96 VP8/90000\r\na=rtcp-fb:96 nack\r\na=rtcp-fb:96 nack pli\r\na=recvonly\r\na=mid:0\r\na=rtcp-mux\r\n'


def test_create_peer_connection() -> None:
	peer_connection = rtc.create_peer_connection()
	datachannel_library = datachannel_module.create_static_library()

	assert peer_connection > 0
	assert datachannel_library.rtcDeletePeerConnection(peer_connection) == 0


def test_add_audio_track() -> None:
	peer_connection = rtc.create_peer_connection()

	assert rtc.add_audio_track(peer_connection, 'sendonly', 111) > 0

	datachannel_module.create_static_library().rtcDeletePeerConnection(peer_connection)


def test_add_video_track() -> None:
	peer_connection = rtc.create_peer_connection()

	assert rtc.add_video_track(peer_connection, 'sendonly', 96) > 0

	datachannel_module.create_static_library().rtcDeletePeerConnection(peer_connection)


def test_negotiate_sdp() -> None:
	datachannel_library = datachannel_module.create_static_library()

	sender_connection = rtc.create_peer_connection()
	rtc.add_video_track(sender_connection, 'sendonly', 96)
	rtc.add_audio_track(sender_connection, 'sendonly', 111)
	sdp_offer = rtc.create_sdp(sender_connection)

	receiver_connection = rtc.create_peer_connection()
	rtc.add_video_track(receiver_connection, 'recvonly', 96)
	rtc.add_audio_track(receiver_connection, 'recvonly', 111)
	sdp_answer = rtc.negotiate_sdp(receiver_connection, sdp_offer)

	assert sdp_answer
	assert 'm=video' in sdp_answer
	assert 'VP8/90000' in sdp_answer
	assert 'm=audio' in sdp_answer
	assert 'opus/48000/2' in sdp_answer

	assert datachannel_library.rtcDeletePeerConnection(sender_connection) == 0
	assert datachannel_library.rtcDeletePeerConnection(receiver_connection) == 0


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
