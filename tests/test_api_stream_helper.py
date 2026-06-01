import asyncio
import ctypes
import struct
import threading
from collections import deque
from unittest.mock import AsyncMock, MagicMock, patch

import cv2
import numpy
import pytest

from facefusion import rtc, rtc_store, state_manager
from facefusion.apis.stream_helper import buffer_audio_frame, buffer_video_frame, create_video_decoder, create_video_encoder, decode_video_frame, destroy_stream, destroy_video_decoder, destroy_video_encoder, encode_video_frame, process_image, process_video, receive_audio_frames, receive_video_frames, receive_vision_frames, run_audio_encode_loop, run_peer_loop, run_video_encode_loop, update_video_encoder_bitrate
from facefusion.codecs import aom_encoder, vpx_encoder
from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download
from facefusion.ffmpeg import read_audio_buffer
from facefusion.hash_helper import create_hash
from facefusion.libraries import aom as aom_module, datachannel as datachannel_module, opus as opus_module, vpx as vpx_module
from facefusion.types import AudioCodec, AudioPack, RtcPeer, RtcPeerAudio, RtcPeerVideo, SessionId, VideoCodec, VideoPack
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
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3'
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

	with patch('facefusion.apis.stream_helper.receive_video_frames'):
		with patch('facefusion.apis.stream_helper.run_video_encode_loop'):
			thread = threading.Thread(target = asyncio.run, args = (run_peer_loop(session_id, rtc_peer),), daemon = True)
			thread.start()
			thread.join(timeout = 5.0)

	assert rtc_store.has_peers(session_id) is False


@pytest.mark.parametrize('video_codec, payload_type', [ ('av1', 35), ('vp8', 96) ])
def test_run_video_encode_loop(video_codec : VideoCodec, payload_type : int) -> None:
	video_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
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
	video_event = threading.Event()

	video_deque.append((video_frame, 0.1))
	video_event.set()

	with patch('facefusion.apis.stream_helper.rtc.send_video') as send_video_mock:
		encode_loop_thread = threading.Thread(target = run_video_encode_loop, args = (rtc_peer, video_deque, video_event), daemon = True)
		encode_loop_thread.start()
		empty_vision_frame = numpy.empty(0)
		video_deque.append((empty_vision_frame, 0.0))
		video_event.set()
		encode_loop_thread.join(timeout = 5.0)

	assert send_video_mock.called

	if video_codec == 'av1':
		if is_linux() or is_windows():
			assert create_hash(send_video_mock.call_args[0][1]) == '9ba7212b'

		if is_macos():
			pytest.skip()

	if video_codec == 'vp8':
		pytest.skip()


def test_run_audio_encode_loop() -> None:
	audio_buffer = read_audio_buffer(get_test_example_file('source.mp3'), 48000, 16, 2)
	audio_frame = numpy.frombuffer(audio_buffer, dtype = numpy.int16).astype(numpy.float32) / 32768.0
	peer_connection = rtc.create_peer_connection()
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

	audio_deque : deque[AudioPack] = deque()
	audio_event = threading.Event()

	audio_deque.append((audio_frame, 0.100))
	audio_event.set()

	encoder_mock = MagicMock()
	encoder_mock.encode.return_value = bytes([ 1 ] * 32)

	with patch('facefusion.apis.stream_helper.opus_encoder.encode', encoder_mock.encode):
		with patch('facefusion.apis.stream_helper.rtc.send_audio') as send_audio_mock:
			audio_loop_thread = threading.Thread(target = run_audio_encode_loop, args = (rtc_peer, audio_deque, audio_event), daemon = True)
			audio_loop_thread.start()
			audio_deque.append((numpy.empty(0), 0.0))
			audio_event.set()
			audio_loop_thread.join(timeout = 5.0)

	assert encoder_mock.encode.called is True
	assert send_audio_mock.called is True


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8' ])
def test_buffer_video_frame(video_codec : VideoCodec) -> None:
	video_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	input_buffer = cv2.cvtColor(video_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	video_encoder = create_video_encoder(video_codec, (426, 226), 1000)
	video_decoder = create_video_decoder(video_codec)
	encode_buffer = encode_video_frame(video_codec, video_encoder, input_buffer, (426, 226), 0)
	video_deque : deque[VideoPack] = deque()
	video_event = threading.Event()

	buffer_video_frame(video_codec, video_decoder, encode_buffer, video_deque, video_event)

	vision_frame, _ = video_deque.popleft()

	assert video_event.is_set()

	if is_linux() or is_windows():
		if video_codec == 'av1':
			assert create_hash(vision_frame.tobytes()) == 'c97d6d29'

		if video_codec == 'vp8':
			assert create_hash(vision_frame.tobytes()) == '99ef2c25'

	if is_macos():
		if video_codec == 'av1':
			assert create_hash(vision_frame.tobytes()) == 'eafd1fab'

		if video_codec == 'vp8':
			assert create_hash(vision_frame.tobytes()) == 'ff3ecb43'


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8' ])
def test_receive_video_frames(video_codec : VideoCodec) -> None:
	video_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_deque : deque[VideoPack] = deque()
	video_event = threading.Event()

	datachannel_library_mock = MagicMock()
	datachannel_library_mock.rtcReceiveMessage.side_effect = [ 0, -1 ]

	with patch('facefusion.apis.stream_helper.datachannel_module.create_static_library', return_value = datachannel_library_mock):
		with patch('facefusion.apis.stream_helper.decode_video_frame', return_value = video_frame):
			rtc_peer_video : RtcPeerVideo =\
			{
				'sender_track': 0,
				'receiver_track': 0,
				'codec': video_codec
			}
			video_receiver_thread = threading.Thread(target = receive_video_frames, args = (rtc_peer_video, video_deque, video_event), daemon = True)
			video_receiver_thread.start()
			video_receiver_thread.join(timeout = 5.0)

	vision_frame, _ = video_deque.popleft()

	if is_linux() or is_windows():
		assert create_hash(vision_frame.tobytes()) == 'a17439db'

	if is_macos():
		assert create_hash(vision_frame.tobytes()) == '38d00e2a'


def test_buffer_audio_frame() -> None:
	audio_buffer = read_audio_buffer(get_test_example_file('source.mp3'), 48000, 16, 2)
	audio_frame = numpy.frombuffer(audio_buffer, dtype = numpy.int16).astype(numpy.float32) / 32768.0
	audio_decoder_mock = MagicMock()
	audio_deque : deque[AudioPack] = deque()
	audio_event = threading.Event()

	with patch('facefusion.apis.stream_helper.decode_audio_frame', return_value = audio_frame.tobytes()):
		buffer_audio_frame('opus', audio_decoder_mock, audio_frame.tobytes(), audio_deque, audio_event)

	buffer_frame, _ = audio_deque.popleft()

	assert audio_event.is_set()
	assert create_hash(buffer_frame.tobytes()) == create_hash(audio_frame.tobytes())


@pytest.mark.parametrize('audio_codec', [ 'opus' ])
def test_receive_audio_frames(audio_codec : AudioCodec) -> None:
	audio_buffer = read_audio_buffer(get_test_example_file('source.mp3'), 48000, 16, 2)
	audio_frame = numpy.frombuffer(audio_buffer, dtype = numpy.int16).astype(numpy.float32) / 32768.0
	audio_deque : deque[AudioPack] = deque()
	audio_event = threading.Event()

	datachannel_library_mock = MagicMock()
	datachannel_library_mock.rtcReceiveMessage.side_effect = [ 0, -1 ]

	with patch('facefusion.apis.stream_helper.datachannel_module.create_static_library', return_value = datachannel_library_mock):
		with patch('facefusion.apis.stream_helper.decode_audio_frame', return_value = audio_frame.tobytes()):
			rtc_peer_audio : RtcPeerAudio =\
			{
				'sender_track': 0,
				'receiver_track': 0,
				'codec': audio_codec
			}
			audio_receiver_thread = threading.Thread(target = receive_audio_frames, args = (rtc_peer_audio, audio_deque, audio_event), daemon = True)
			audio_receiver_thread.start()
			audio_receiver_thread.join(timeout = 5.0)

	buffer_frame, _ = audio_deque.popleft()

	assert create_hash(buffer_frame.tobytes()) == create_hash(audio_frame.tobytes())


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8' ])
def test_encode_and_decode_video_frame(video_codec : VideoCodec) -> None:
	video_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	input_buffer = cv2.cvtColor(video_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
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
	video_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	input_buffer = cv2.cvtColor(video_frame, cv2.COLOR_BGR2YUV_I420).tobytes()

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
	video_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	input_buffer = cv2.cvtColor(video_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
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
