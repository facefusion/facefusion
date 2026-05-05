import threading

import pytest

from facefusion import rtc
from .stream_helper import create_sdp_offer


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	if rtc.create_static_rtc_library() is None:
		pytest.skip('libdatachannel binary not available')


def test_on_sdp_ready() -> None:
	event = threading.Event()
	rtc._on_sdp_ready(1, b'v=0\r\n', 0, id(event))

	assert event.is_set()


def test_negotiate_sdp() -> None:
	peer_connection = rtc.create_peer_connection()
	sdp_offer = create_sdp_offer()
	result = rtc.negotiate_sdp(peer_connection, sdp_offer)
	rtc.create_static_rtc_library().rtcDeletePeerConnection(peer_connection)

	assert result and result.startswith('v=0')
