import ctypes
import struct
import threading
from collections import deque
from unittest.mock import MagicMock, patch

import cv2
import numpy
import pytest

from facefusion import rtc, rtc_store, state_manager
from facefusion.apis.stream_video import create_video_decoder, create_video_encoder, decode_video_frame, destroy_video_decoder, destroy_video_encoder, encode_video_frame, fill_video_deque, receive_video_frames, run_video_encode_loop, update_video_encoder_bitrate
from facefusion.codecs import aom_encoder, vpx_encoder
from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download
from facefusion.hash_helper import create_hash
from facefusion.libraries import aom as aom_module, datachannel as datachannel_module, vpx as vpx_module
from facefusion.types import RtcPeer, RtcPeerVideo, VideoCodec, VideoPack
from facefusion.vision import read_video_frame
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])
	state_manager.init_item('processors', [])

	aom_module.pre_check()
	vpx_module.pre_check()
	datachannel_module.pre_check()

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	rtc_store.clear()


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
		'receiver_bitrate': ctypes.c_uint(8000)
	}

	video_deque : deque[VideoPack] = deque()
	video_event = threading.Event()

	video_deque.append((video_frame, 0.1))
	video_event.set()

	with patch('facefusion.apis.stream_video.rtc.send_video') as send_video_mock:
		encode_loop_thread = threading.Thread(target = run_video_encode_loop, args = (rtc_peer, video_deque, video_event), daemon = True)
		encode_loop_thread.start()
		empty_vision_frame = numpy.empty(0)
		video_deque.append((empty_vision_frame, 0.0))
		video_event.set()
		encode_loop_thread.join(timeout = 5.0)

	assert send_video_mock.called

	if video_codec == 'av1':
		if is_linux() or is_windows():
			assert create_hash(send_video_mock.call_args[0][1]) == 'cc6a35cc'

		if is_macos():
			pytest.skip()

	if video_codec == 'vp8':
		pytest.skip()


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8' ])
def test_receive_video_frames(video_codec : VideoCodec) -> None:
	video_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_deque : deque[VideoPack] = deque()
	video_event = threading.Event()

	datachannel_library_mock = MagicMock()
	datachannel_library_mock.rtcReceiveMessage.side_effect = [ 0, -1 ]

	with patch('facefusion.apis.stream_video.datachannel_module.create_static_library', return_value = datachannel_library_mock):
		with patch('facefusion.apis.stream_video.decode_video_frame', return_value = video_frame):
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


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8' ])
def test_fill_video_deque(video_codec : VideoCodec) -> None:
	video_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	input_buffer = cv2.cvtColor(video_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	video_encoder = create_video_encoder(video_codec, (426, 226), 1000)
	video_decoder = create_video_decoder(video_codec)
	encode_buffer = encode_video_frame(video_codec, video_encoder, input_buffer, (426, 226), 0)
	video_deque : deque[VideoPack] = deque()
	video_event = threading.Event()

	fill_video_deque(video_codec, video_decoder, encode_buffer, video_deque, video_event)

	vision_frame, _ = video_deque.popleft()

	assert video_event.is_set()

	if is_linux() or is_windows():
		if video_codec == 'av1':
			assert create_hash(vision_frame.tobytes()) == 'b5b6486d'

		if video_codec == 'vp8':
			assert create_hash(vision_frame.tobytes()) == '99ef2c25'

	if is_macos():
		if video_codec == 'av1':
			assert create_hash(vision_frame.tobytes()) == '74e9926f'

		if video_codec == 'vp8':
			assert create_hash(vision_frame.tobytes()) == 'ff3ecb43'


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
			assert create_hash(decode_buffer) == 'b5b6486d'

		if video_codec == 'vp8':
			assert create_hash(decode_buffer) == '99ef2c25'

	if is_macos():
		if video_codec == 'av1':
			assert create_hash(decode_buffer) == '74e9926f'

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
