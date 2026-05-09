import ctypes
import threading
import time
from typing import Optional

from starlette.testclient import TestClient

from facefusion import rtc
from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import SdpOffer


def create_sdp_offer() -> Optional[SdpOffer]:
	datachannel_library = datachannel_module.create_static_library()
	peer_connection = rtc.create_peer_connection(disable_auto_negotiation = True)

	datachannel_library.rtcAddTrack(peer_connection, rtc.build_media_description('video', 96, 'VP8/90000', 'recvonly', 0))
	datachannel_library.rtcAddTrack(peer_connection, rtc.build_media_description('audio', 111, 'opus/48000/2', 'recvonly', 1))
	datachannel_library.rtcSetLocalDescription(peer_connection, b'offer')

	buffer_size = 16384
	buffer_string = ctypes.create_string_buffer(buffer_size)
	wait_limit = time.monotonic() + 5

	while time.monotonic() < wait_limit:
		if datachannel_library.rtcGetLocalDescription(peer_connection, buffer_string, buffer_size) > 0:
			sdp = buffer_string.value.decode()
			datachannel_library.rtcDeletePeerConnection(peer_connection)
			return sdp

		time.sleep(0.05)

	datachannel_library.rtcDeletePeerConnection(peer_connection)
	return None


def open_websocket_stream(test_client : TestClient, subprotocols : list[str], source_content : bytes, ready_event : threading.Event, stop_event : threading.Event) -> None:
	with test_client.websocket_connect('/stream', subprotocols = subprotocols) as websocket:
		websocket.send_bytes(source_content)
		websocket.receive_text()
		ready_event.set()
		stop_event.wait()
