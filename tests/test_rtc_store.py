from typing import List

import pytest

from facefusion import rtc, rtc_store, state_manager
from facefusion.libraries import datachannel as datachannel_module, opus as opus_module, vpx as vpx_module
from facefusion.types import RtcPeer


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])

	datachannel_module.pre_check()
	opus_module.pre_check()
	vpx_module.pre_check()


@pytest.fixture(autouse = True)
def before_each() -> None:
	rtc_store.RTC_STORE.clear()


# TODO: needs review
def test_create_rtc_peers() -> None:
	rtc_store.create_rtc_peers('test-session')

	assert rtc_store.RTC_STORE.get('test-session') == []


# TODO: needs review
def test_get_rtc_peers() -> None:
	assert rtc_store.get_rtc_peers('test-session') is None

	rtc_store.create_rtc_peers('test-session')

	assert rtc_store.get_rtc_peers('test-session') == []


# TODO: needs review
def test_destroy_rtc_peers() -> None:
	rtc_store.create_rtc_peers('test-session')
	rtc_store.destroy_rtc_peers('test-session')

	assert rtc_store.get_rtc_peers('test-session') is None


# TODO: needs review
def test_destroy_rtc_peers_with_connections() -> None:
	datachannel_library = datachannel_module.create_static_library()
	peer_connection = rtc.create_peer_connection()
	rtc_store.create_rtc_peers('test-session')
	rtc_peers : List[RtcPeer] =\
	[
		{
			'peer_connection': peer_connection,
			'video_track': 0,
			'audio_track': 0
		}
	]
	rtc_store.RTC_STORE['test-session'] = rtc_peers

	rtc_store.destroy_rtc_peers('test-session')

	assert rtc_store.get_rtc_peers('test-session') is None
	assert datachannel_library.rtcDeletePeerConnection(peer_connection) < 0
