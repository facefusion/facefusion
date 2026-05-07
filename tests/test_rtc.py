import ctypes
import time
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
	peer_connection = rtc.create_peer_connection()
	audio_track = rtc.add_audio_track(peer_connection, 'sendonly')
	rtc_library = rtc.create_static_rtc_library()

	assert audio_track > 0
	assert rtc_library.rtcDeletePeerConnection(peer_connection) == 0


def test_add_video_track() -> None:
	peer_connection = rtc.create_peer_connection()
	video_track = rtc.add_video_track(peer_connection, 'sendonly')
	rtc_library = rtc.create_static_rtc_library()

	assert video_track > 0
	assert rtc_library.rtcDeletePeerConnection(peer_connection) == 0


def test_peer_connection_open_and_close() -> None:
	rtc_library = rtc.create_static_rtc_library()

	peer_1 = rtc.create_peer_connection(enable_ice_udp_mux = False)
	video_track = rtc.add_video_track(peer_1, 'sendonly')
	rtc_library.rtcSetLocalDescription(peer_1, b'offer')
	buffer_size = 16384
	buffer_string = ctypes.create_string_buffer(buffer_size)
	wait_limit = time.monotonic() + 5
	offer = None

	while time.monotonic() < wait_limit:
		if rtc_library.rtcGetLocalDescription(peer_1, buffer_string, buffer_size) > 0:
			offer = buffer_string.value.decode()
			break
		time.sleep(0.05)

	peer_2 = rtc.create_peer_connection(enable_ice_udp_mux = False)
	rtc.add_video_track(peer_2, 'recvonly')
	answer = rtc.negotiate_sdp(peer_2, offer)
	rtc_library.rtcSetRemoteDescription(peer_1, answer.encode('utf-8'), b'answer')

	wait_limit = time.monotonic() + 5
	while time.monotonic() < wait_limit and not rtc_library.rtcIsOpen(video_track):
		time.sleep(0.05)

	assert rtc_library.rtcIsOpen(video_track) is True
	assert rtc_library.rtcDeletePeerConnection(peer_1) == 0
	assert rtc_library.rtcDeletePeerConnection(peer_2) == 0
	assert rtc_library.rtcIsOpen(video_track) is False
