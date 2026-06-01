import asyncio
import ctypes
import struct
import threading
import time
from collections import deque
from unittest.mock import AsyncMock, MagicMock, patch

import cv2
import numpy
import pytest

from facefusion import rtc, rtc_store, state_manager
from facefusion.apis.stream_helper import create_video_decoder, create_video_encoder, decode_video_frame, destroy_stream, destroy_video_decoder, destroy_video_encoder, encode_video_frame, process_image, process_video, receive_audio_frames, receive_video_frames, receive_vision_frames, run_encode_loop, run_peer_loop, update_video_encoder_bitrate
from facefusion.codecs import aom_encoder, vpx_encoder
from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download
from facefusion.hash_helper import create_hash
from facefusion.libraries import aom as aom_module, datachannel as datachannel_module, opus as opus_module, vpx as vpx_module
from facefusion.types import AudioPack, RtcPeer, VideoCodec, VideoPack
from facefusion.vision import read_video_frame
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])
	state_manager.init_item('processors', [])

	aom_module.pre_check()
	vpx_module.pre_check()
	opus_module.pre_check()
	datachannel_module.pre_check()

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg'
	])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	rtc_store.clear()


@pytest.mark.anyio
async def test_process_image() -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	frame_buffer = cv2.imencode('.jpg', vision_frame)[1].tobytes()
	websocket_mock = AsyncMock()
	websocket_mock.receive.side_effect =\
	[
		{
			'type': 'websocket.receive',
			'bytes': frame_buffer
		}
	]

	state_manager.init_item('source_paths', [ get_test_example_file('source.jpg') ])
	await process_image(websocket_mock)

	websocket_mock.send_bytes.assert_called_once()
	assert websocket_mock.send_bytes.call_args[0][0][:3] == bytes([ 255, 216, 255 ])

	state_manager.init_item('source_paths', None)
	await process_image(websocket_mock)

	websocket_mock.send_bytes.assert_called_once()


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

	with patch('facefusion.apis.stream_helper.threading.Thread'):
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
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	frame_buffer = cv2.imencode('.jpg', vision_frame)[1].tobytes()
	websocket_mock = AsyncMock()
	websocket_mock.receive.side_effect =\
	[
		{
			'type': 'websocket.receive',
			'bytes': frame_buffer
		},
		{
			'type': 'websocket.receive',
			'bytes': 'invalid'.encode()
		},
		{
			'type': 'websocket.receive',
			'bytes': frame_buffer
		},
		{
			'type': 'websocket.disconnect'
		}
	]

	frames = []

	async for frame in receive_vision_frames(websocket_mock):
		frames.append(frame)

	assert len(frames) == 2
	assert frames[0].shape == vision_frame.shape


@pytest.mark.parametrize('video_codec, payload_type', [ ('av1', 35), ('vp8', 96) ])
def test_run_peer_loop(video_codec : VideoCodec, payload_type : int) -> None:
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

	session_id = 'test-run-peer-loop-' + video_codec
	rtc_store.init_peers(session_id)
	rtc_store.get_peers(session_id).append(rtc_peer)

	with patch('facefusion.apis.stream_helper.receive_video_frames'):
		with patch('facefusion.apis.stream_helper.run_encode_loop') as mock_encode_loop:
			thread = threading.Thread(target = asyncio.run, args = (run_peer_loop(session_id, rtc_peer),), daemon = True)
			thread.start()
			thread.join(timeout = 5.0)

	assert mock_encode_loop.called
	assert mock_encode_loop.call_args[0][1] == video_codec
	assert rtc_store.has_peers(session_id) is False


@pytest.mark.parametrize('video_codec, payload_type', [ ('av1', 35), ('vp8', 96) ])
def test_run_encode_loop(video_codec : VideoCodec, payload_type : int) -> None:
	source_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
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

	video_deque : deque[VideoPack] = deque()
	audio_deque : deque[AudioPack] = deque()
	video_event = threading.Event()

	video_deque.append((source_frame, 0.100))
	video_event.set()

	with patch('facefusion.apis.stream_helper.rtc.send_video') as mock_send_video:
		thread = threading.Thread(target = run_encode_loop, args = (rtc_peer, video_codec, video_deque, audio_deque, video_event), daemon = True)
		thread.start()
		time.sleep(0.1)
		video_deque.append((numpy.empty(0), 0.0))
		video_event.set()
		thread.join(timeout = 5.0)

	assert mock_send_video.called
	assert len(mock_send_video.call_args[0][1]) > 0


@pytest.mark.parametrize('video_codec, payload_type', [ ('av1', 35), ('vp8', 96) ])
def test_run_peer_loop_send_order(video_codec : VideoCodec, payload_type : int) -> None:
	source_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	audio_frame = numpy.zeros(960 * 2, dtype = numpy.float32)
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

	video_deque : deque[VideoPack] = deque()
	audio_deque : deque[AudioPack] = deque()
	video_event = threading.Event()

	video_deque.append((source_frame, 0.100))
	audio_deque.append((audio_frame, 0.100))
	video_event.set()

	manager = MagicMock()
	manager.process_frame.return_value = source_frame
	manager.opus_encode.return_value = bytes([ 1 ] * 32)

	with patch('facefusion.apis.stream_helper.streamer.process_frame', manager.process_frame):
		with patch('facefusion.apis.stream_helper.opus_encoder.encode', manager.opus_encode):
			with patch('facefusion.apis.stream_helper.rtc.send_audio', manager.send_audio):
				with patch('facefusion.apis.stream_helper.rtc.send_video', manager.send_video):
					thread = threading.Thread(target = run_encode_loop, args = (rtc_peer, video_codec, video_deque, audio_deque, video_event), daemon = True)
					thread.start()
					time.sleep(0.1)
					video_deque.append((numpy.empty(0), 0.0))
					video_event.set()
					thread.join(timeout = 5.0)

	call_names = [ call[0] for call in manager.mock_calls ]

	assert 'process_frame' in call_names and 'send_audio' in call_names
	assert call_names.index('process_frame') < call_names.index('send_audio')


def test_receive_video_frames() -> None:
	datachannel_library_mock = MagicMock()
	datachannel_library_mock.rtcReceiveMessage.side_effect = [ 0, -1 ]
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_deque : deque[VideoPack] = deque()
	video_event = threading.Event()

	with patch('facefusion.apis.stream_helper.datachannel_module.create_static_library', return_value = datachannel_library_mock):
		with patch('facefusion.apis.stream_helper.decode_video_frame', return_value = vision_frame):
			receiver_thread = threading.Thread(target = receive_video_frames, args = (0, 'vp8', video_deque, video_event), daemon = True)
			receiver_thread.start()
			receiver_thread.join(timeout = 2.0)

	if is_linux() or is_windows():
		assert create_hash(video_deque[0][0].tobytes()) == 'a17439db'

	if is_macos():
		assert create_hash(video_deque[0][0].tobytes()) == '38d00e2a'


def test_receive_audio_frames() -> None:
	datachannel_library_mock = MagicMock()
	datachannel_library_mock.rtcReceiveMessage.side_effect = [ 0, -1 ]
	audio_data = numpy.zeros(960 * 2, dtype = numpy.float32)
	audio_deque : deque[AudioPack] = deque()

	with patch('facefusion.apis.stream_helper.datachannel_module.create_static_library', return_value = datachannel_library_mock):
		with patch('facefusion.apis.stream_helper.opus_decoder.decode', return_value = audio_data.tobytes()):
			receiver_thread = threading.Thread(target = receive_audio_frames, args = (0, 'opus', audio_deque), daemon = True)
			receiver_thread.start()
			receiver_thread.join(timeout = 2.0)

	assert audio_deque[0][0].dtype == numpy.float32
	assert audio_deque[0][0].size == 960 * 2
	assert len(audio_deque) == 1


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8' ])
def test_encode_and_decode_video_frame(video_codec : VideoCodec) -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	input_buffer = cv2.cvtColor(vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	video_encoder = create_video_encoder(video_codec, (426, 226), 1000)
	video_decoder = create_video_decoder(video_codec)
	encode_buffer = encode_video_frame(video_codec, video_encoder, input_buffer, (426, 226), 0)
	decode_buffer = decode_video_frame(video_codec, video_decoder, encode_buffer).tobytes()

	if is_linux() or is_windows():
		if video_codec == 'av1':
			assert create_hash(decode_buffer) == 'c97d6d29'

		if video_codec == 'vp8':
			assert create_hash(decode_buffer) == '99ef2c25'

	if is_macos():
		if video_codec == 'av1':
			assert create_hash(decode_buffer) == 'eafd1fab'

		if video_codec == 'vp8':
			assert create_hash(decode_buffer) == 'ff3ecb43'

	assert decode_video_frame(video_codec, video_decoder, bytes()) is None


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8' ])
def test_create_and_destroy_video_decoder(video_codec : VideoCodec) -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	input_buffer = cv2.cvtColor(vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()

	if video_codec == 'av1':
		video_encoder = aom_encoder.create((426, 226), 1000, 1, 0)
		encode_buffer = aom_encoder.encode(video_encoder, input_buffer, (426, 226), 0)

	if video_codec == 'vp8':
		video_encoder = vpx_encoder.create((426, 226), 1000, 1, 0)
		encode_buffer = vpx_encoder.encode(video_encoder, input_buffer, (426, 226), 0)

	video_decoder = create_video_decoder(video_codec)

	assert numpy.any(decode_video_frame(video_codec, video_decoder, encode_buffer))

	destroy_video_decoder(video_codec, video_decoder)

	assert decode_video_frame(video_codec, video_decoder, encode_buffer) is None


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8' ])
def test_create_and_destroy_video_encoder(video_codec : VideoCodec) -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	input_buffer = cv2.cvtColor(vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()

	video_encoder = create_video_encoder(video_codec, (426, 226), 4000)

	if video_codec == 'av1':
		assert aom_encoder.encode(video_encoder, input_buffer, (426, 226), 0)

	if video_codec == 'vp8':
		assert vpx_encoder.encode(video_encoder, input_buffer, (426, 226), 0)

	destroy_video_encoder(video_codec, video_encoder)

	if video_codec == 'av1':
		assert aom_encoder.encode(video_encoder, input_buffer, (426, 226), 1) == bytes()

	if video_codec == 'vp8':
		assert vpx_encoder.encode(video_encoder, input_buffer, (426, 226), 1) == bytes()


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8' ])
def test_update_video_encoder_bitrate(video_codec : VideoCodec) -> None:
	video_encoder = create_video_encoder(video_codec, (426, 226), 4000)

	if video_codec == 'av1':
		assert struct.unpack_from('I', video_encoder, 128 + 136)[0] == 4000

	if video_codec == 'vp8':
		assert struct.unpack_from('I', video_encoder, 64 + 112)[0] == 4000

	assert update_video_encoder_bitrate(video_codec, video_encoder, 6000)

	if video_codec == 'av1':
		assert struct.unpack_from('I', video_encoder, 128 + 136)[0] == 6000

	if video_codec == 'vp8':
		assert struct.unpack_from('I', video_encoder, 64 + 112)[0] == 6000

	destroy_video_encoder(video_codec, video_encoder)


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
