import asyncio
import ctypes
import threading
from unittest.mock import AsyncMock, patch

import pytest

from facefusion import rtc, rtc_store, state_manager
from facefusion.apis.stream_manager import destroy_stream, process_image, process_video, receive_vision_frames, run_peer_loop
from facefusion.common_helper import is_linux, is_windows
from facefusion.download import conditional_download
from facefusion.hash_helper import create_hash
from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import RtcPeer, SessionId, VideoCodec
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])
	state_manager.init_item('processors', [])

	datachannel_module.pre_check()

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg'
	])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	rtc_store.clear()


@pytest.mark.anyio
async def test_process_image() -> None:
	image_buffer = open(get_test_example_file('source.jpg'), 'rb').read()
	websocket_mock = AsyncMock()
	websocket_mock.receive.side_effect =\
	[
		{
			'type': 'websocket.receive',
			'bytes': image_buffer
		}
	]

	await process_image(websocket_mock)

	websocket_mock.send_bytes.assert_called_once()

	if is_linux() or is_windows():
		assert create_hash(websocket_mock.send_bytes.call_args[0][0]) == '0142782f'


@pytest.mark.parametrize('video_codec, session_id', [ ('av1', 'test-process-video-av1'), ('vp8', 'test-process-video-vp8') ])
def test_process_video(video_codec : VideoCodec, session_id : str) -> None:
	peer_connection = rtc.create_peer_connection()

	if video_codec == 'av1':
		rtc.add_video_track(peer_connection, 'sendrecv', video_codec, 35)

	if video_codec == 'vp8':
		rtc.add_video_track(peer_connection, 'sendrecv', video_codec, 96)

	rtc.add_audio_track(peer_connection, 'sendrecv', 'opus', 111)
	sdp_offer = rtc.create_sdp_offer(peer_connection)
	datachannel_module.create_static_library().rtcDeletePeerConnection(peer_connection)

	with patch('facefusion.apis.stream_manager.threading.Thread'):
		sdp_answer = process_video(session_id, sdp_offer)

	assert sdp_answer
	assert 'm=video' in sdp_answer
	assert 'a=recvonly' in sdp_answer
	assert 'a=sendonly' in sdp_answer

	for peer in rtc_store.get_peers(session_id):
		sender_bitrate = peer.get('sender_bitrate')
		receiver_bitrate = peer.get('receiver_bitrate')

		assert sender_bitrate.value == 0
		assert receiver_bitrate.value == 0

		rtc.handle_remb(0, 8000000, ctypes.addressof(sender_bitrate))
		assert sender_bitrate.value == 8000

		rtc.handle_remb(0, 4000000, ctypes.addressof(receiver_bitrate))
		assert receiver_bitrate.value == 4000


@pytest.mark.anyio
async def test_receive_vision_frames() -> None:
	image_buffer = open(get_test_example_file('source.jpg'), 'rb').read()
	websocket_mock = AsyncMock()
	websocket_mock.receive.side_effect =\
	[
		{
			'type': 'websocket.receive',
			'bytes': image_buffer
		},
		{
			'type': 'websocket.receive',
			'bytes': 'invalid'.encode()
		},
		{
			'type': 'websocket.disconnect'
		}
	]

	vision_frames = receive_vision_frames(websocket_mock)

	assert create_hash((await anext(vision_frames)).tobytes()) == '5ed32ca0'


@pytest.mark.parametrize('video_codec, payload_type, session_id', [ ('av1', 35, 'test-run-peer-loop-av1'), ('vp8', 96, 'test-run-peer-loop-vp8') ])
def test_run_peer_loop(video_codec : VideoCodec, payload_type : int, session_id : SessionId) -> None:
	peer_connection = rtc.create_peer_connection()
	video_sender_track = rtc.add_video_track(peer_connection, 'sendonly', video_codec, payload_type)
	video_receiver_track = rtc.add_video_track(peer_connection, 'recvonly', video_codec, payload_type)
	rtc_peer : RtcPeer =\
	{
		'peer_connection': peer_connection,
		'video':
		{
			'sender_track': video_sender_track,
			'receiver_track': video_receiver_track,
			'codec': video_codec
		},
		'sender_bitrate': ctypes.c_uint(0),
		'receiver_bitrate': ctypes.c_uint(0)
	}

	rtc_store.init_peers(session_id)
	rtc_store.get_peers(session_id).append(rtc_peer)

	assert rtc_store.has_peers(session_id) is True

	with patch('facefusion.apis.stream_manager.receive_video_frames'):
		with patch('facefusion.apis.stream_manager.run_video_encode_loop'):
			thread = threading.Thread(target = asyncio.run, args = (run_peer_loop(session_id, rtc_peer),), daemon = True)
			thread.start()
			thread.join(timeout = 5.0)

	assert rtc_store.has_peers(session_id) is False


def test_destroy_stream() -> None:
	peer_connection = rtc.create_peer_connection()
	rtc.add_video_track(peer_connection, 'sendonly', 'vp8', 96)
	rtc_peer : RtcPeer =\
	{
		'peer_connection': peer_connection,
		'video':
		{
			'sender_track': 0,
			'receiver_track': 0,
			'codec': 'vp8'
		},
		'sender_bitrate': ctypes.c_uint(0),
		'receiver_bitrate': ctypes.c_uint(0)
	}
	session_id = 'test-destroy-stream'

	rtc_store.init_peers(session_id)
	rtc_store.get_peers(session_id).append(rtc_peer)

	assert destroy_stream(session_id) is True
	assert rtc_store.get_peers(session_id) is None

	assert destroy_stream(session_id) is False
