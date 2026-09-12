import ctypes
from typing import Iterator

import pytest

from facefusion import rtc, session_context, session_manager, state_manager
from facefusion.libraries import datachannel as datachannel_module
from facefusion.rtc_store import delete_peer, get_peer, has_peer, init, set_peer
from facefusion.types import RtcPeer


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])

	datachannel_module.pre_check()


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = session_context.resolve_local_id()

	session_context.set_session_id(local_id)
	init()

	yield

	delete_peer()
	session_context.set_session_id(local_id)


def create_rtc_peer() -> RtcPeer:
	peer_connection = rtc.create_peer_connection()
	rtc_peer : RtcPeer =\
	{
		'peer_connection': peer_connection,
		'video':
		{
			'sender_track': rtc.add_video_track(peer_connection, 'sendonly', 'vp8', 96),
			'receiver_track': 0,
			'codec': 'vp8'
		},
		'sender_bitrate': ctypes.c_uint(0),
		'receiver_bitrate': ctypes.c_uint(0)
	}

	return rtc_peer


def test_init() -> None:
	local_id = session_context.resolve_local_id()
	rtc_peer = create_rtc_peer()

	set_peer(rtc_peer)
	session_context.set_session_id('session-a')
	init()

	assert has_peer() is False

	session_manager.fork_session()

	assert has_peer() is False

	session_manager.join_session()
	session_context.set_session_id(local_id)

	assert get_peer() is rtc_peer

	session_context.set_session_id('session-a')
	set_peer(create_rtc_peer())
	session_manager.fork_session()

	assert has_peer() is True

	session_manager.join_session()
	delete_peer()
	session_context.set_session_id(local_id)


def test_has_peer() -> None:
	assert has_peer() is False

	set_peer(create_rtc_peer())

	assert has_peer() is True


def test_get_peer() -> None:
	rtc_peer = create_rtc_peer()

	assert get_peer() is None

	set_peer(rtc_peer)

	assert get_peer() is rtc_peer


def test_set_peer() -> None:
	rtc_peer = create_rtc_peer()

	set_peer(rtc_peer)

	assert get_peer() is rtc_peer


def test_delete_peer() -> None:
	set_peer(create_rtc_peer())
	delete_peer()

	assert has_peer() is False
	assert get_peer() is None
