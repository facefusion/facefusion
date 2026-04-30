import ctypes
import os
import threading
import time
from typing import Optional

from starlette.testclient import TestClient

from facefusion import rtc
from facefusion.types import RtcSdpOffer


# TODO: reuse media description building from rtc.py
def create_sdp_offer() -> Optional[RtcSdpOffer]:
	rtc_library = rtc.create_static_rtc_library()
	peer_connection = rtc.create_peer_connection(disable_auto_negotiation = True)

	media_video = os.linesep.join(
	[
		'm=video 9 UDP/TLS/RTP/SAVPF 96',
		'a=rtpmap:96 VP8/90000',
		'a=recvonly',
		'a=mid:0',
		''
	]).encode()
	media_audio = os.linesep.join(
	[
		'm=audio 9 UDP/TLS/RTP/SAVPF 111',
		'a=rtpmap:111 opus/48000/2',
		'a=recvonly',
		'a=mid:1',
		''
	]).encode()

	rtc_library.rtcAddTrack(peer_connection, media_video)
	rtc_library.rtcAddTrack(peer_connection, media_audio)
	rtc_library.rtcSetLocalDescription(peer_connection, b'offer')

	buffer_size = 16384
	buffer_string = ctypes.create_string_buffer(buffer_size)
	wait_limit = time.monotonic() + 5

	while time.monotonic() < wait_limit:
		if rtc_library.rtcGetLocalDescription(peer_connection, buffer_string, buffer_size) > 0:
			sdp = buffer_string.value.decode()
			rtc_library.rtcDeletePeerConnection(peer_connection)
			#TODO: use return buffer_string.value.decode()
			return sdp

		time.sleep(0.05)

	rtc_library.rtcDeletePeerConnection(peer_connection)
	return None


def open_websocket_stream(test_client : TestClient, subprotocols : list[str], source_content : bytes, ready_event : threading.Event, stop_event : threading.Event) -> None:
	with test_client.websocket_connect('/stream', subprotocols = subprotocols) as websocket:
		websocket.send_bytes(source_content)
		websocket.receive_text()
		ready_event.set()
		stop_event.wait()
