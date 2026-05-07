import pytest

from facefusion import rtc


@pytest.fixture(scope = 'module')
def before_all() -> None:
	rtc.pre_check()


def test_build_media_description() -> None:
	assert rtc.build_media_description('audio', 111, 'opus/48000/2', 'sendonly', 1) == b'm=audio 9 UDP/TLS/RTP/SAVPF 111\r\na=rtpmap:111 opus/48000/2\r\na=sendonly\r\na=mid:1\r\na=rtcp-mux\r\n'
	assert rtc.build_media_description('video', 96, 'VP8/90000', 'recvonly', 0) == b'm=video 9 UDP/TLS/RTP/SAVPF 96\r\na=rtpmap:96 VP8/90000\r\na=recvonly\r\na=mid:0\r\na=rtcp-mux\r\n'


def test_create_peer_connection() -> None:
	peer_connection = rtc.create_peer_connection()
	rtc_library = rtc.create_static_rtc_library()

	assert peer_connection > 0
	assert rtc_library.rtcDeletePeerConnection(peer_connection) == 0


def test_add_audio_track() -> None:
	rtc_library = rtc.create_static_rtc_library()

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

	assert rtc_library.rtcDeletePeerConnection(sender_connection) == 0
	assert rtc_library.rtcDeletePeerConnection(receiver_connection) == 0


def test_add_video_track() -> None:
	rtc_library = rtc.create_static_rtc_library()

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

	assert rtc_library.rtcDeletePeerConnection(sender_connection) == 0
	assert rtc_library.rtcDeletePeerConnection(receiver_connection) == 0
