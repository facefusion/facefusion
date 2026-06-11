import ctypes
import struct
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from functools import partial
from queue import Queue
from typing import Callable, Tuple
from unittest.mock import MagicMock, patch

import cv2
import numpy
import pytest

from facefusion import rtc, rtc_store, state_manager
from facefusion.apis.stream_video import create_video_decoder, create_video_encoder, decode_video_frame, destroy_video_decoder, destroy_video_encoder, encode_video_frame, handle_video_frame, process_video_frame, receive_video_frames, run_video_encode_loop, update_video_encoder_bitrate, update_video_encoder_resolution
from facefusion.codecs import aom_encoder, vpx_encoder
from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download
from facefusion.hash_helper import create_hash
from facefusion.libraries import aom as aom_module, datachannel as datachannel_module, vpx as vpx_module
from facefusion.types import BufferPack, RtcPeer, RtcPeerVideo, Time, VideoCodec
from facefusion.vision import read_video_frame
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])
	state_manager.init_item('execution_thread_count', 8)
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


def set_ready_event(ready_event : threading.Event, track : int, close_callback : Callable[[int, ctypes.c_void_p], None]) -> None:
	ready_event.set()


@pytest.mark.parametrize('video_codec, payload_type', [ ('av1', 35), ('vp8', 96), ('vp9', 98) ])
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

	video_queue : Queue[Tuple[Time, Future[BufferPack]]] = Queue(maxsize = 30)

	with ThreadPoolExecutor(max_workers = 1) as executor:
		video_queue.put((0.1, executor.submit(process_video_frame, video_frame)))

		with patch('facefusion.apis.stream_video.rtc.send_video') as send_video_mock:
			encode_loop_thread = threading.Thread(target = run_video_encode_loop, args = (rtc_peer, video_queue), daemon = True)
			encode_loop_thread.start()
			empty_future : Future[BufferPack] = Future()
			empty_future.set_result(BufferPack(buffer = bytes(), resolution = (0, 0)))
			video_queue.put((0.0, empty_future))
			encode_loop_thread.join(timeout = 5.0)

	assert send_video_mock.called

	if video_codec == 'av1':
		if is_linux() or is_windows():
			assert create_hash(send_video_mock.call_args[0][1]) == 'cc6a35cc'

		if is_macos():
			pytest.skip()

	if video_codec == 'vp8':
		pytest.skip()

	if video_codec == 'vp9':
		pytest.skip()


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8', 'vp9' ])
def test_receive_video_frames(video_codec : VideoCodec) -> None:
	video_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_queue : Queue[Tuple[Time, Future[BufferPack]]] = Queue(maxsize = 30)

	datachannel_mock = MagicMock()
	ready_event = threading.Event()
	datachannel_mock.rtcSetClosedCallback.side_effect = partial(set_ready_event, ready_event)

	with ThreadPoolExecutor(max_workers = 1) as executor:
		with patch('facefusion.libraries.datachannel.create_static_library', return_value = datachannel_mock):
			with patch('facefusion.apis.stream_video.decode_video_frame', return_value = video_frame):
				with patch('facefusion.apis.stream_video.process_video_frame', return_value = BufferPack(buffer = video_frame.tobytes(), resolution = (426, 226))):
					rtc_peer_video : RtcPeerVideo =\
					{
						'sender_track': 0,
						'receiver_track': 0,
						'codec': video_codec
					}
					video_receiver_thread = threading.Thread(target = receive_video_frames, args = (rtc_peer_video, video_queue, executor), daemon = True)
					video_receiver_thread.start()
					ready_event.wait(timeout = 5.0)
					datachannel_mock.rtcSetFrameCallback.call_args[0][1](0, bytes([ 0 ]), 1, None, None)
					datachannel_mock.rtcSetClosedCallback.call_args[0][1](0, None)
					video_receiver_thread.join(timeout = 5.0)
					_, video_future = video_queue.get_nowait()

	video_buffer = video_future.result().get('buffer')

	if is_linux() or is_windows():
		assert create_hash(video_buffer) == 'a17439db'

	if is_macos():
		assert create_hash(video_buffer) == '38d00e2a'


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8', 'vp9' ])
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

		if video_codec == 'vp9':
			assert create_hash(decode_buffer) == 'f2d3e3fb'

	if is_macos():
		if video_codec == 'av1':
			assert create_hash(decode_buffer) == 'eafd1fab'

		if video_codec == 'vp8':
			assert create_hash(decode_buffer) == 'ff3ecb43'

		if video_codec == 'vp9':
			assert create_hash(decode_buffer) == 'a994fa02'

	assert decode_video_frame(video_codec, video_decoder, bytes()) is None


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8', 'vp9' ])
def test_create_and_destroy_video_decoder(video_codec : VideoCodec) -> None:
	video_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	input_buffer = cv2.cvtColor(video_frame, cv2.COLOR_BGR2YUV_I420).tobytes()

	if video_codec == 'av1':
		video_encoder = aom_encoder.create((426, 226), 1000, 1, 0)
		encode_buffer = aom_encoder.encode(video_encoder, input_buffer, (426, 226), 0)
	if video_codec in [ 'vp8', 'vp9' ]:
		video_encoder = vpx_encoder.create(video_codec, (426, 226), 1000, 1, 0) #type:ignore[arg-type]
		encode_buffer = vpx_encoder.encode(video_encoder, input_buffer, (426, 226), 0)

	video_decoder = create_video_decoder(video_codec)

	assert numpy.any(decode_video_frame(video_codec, video_decoder, encode_buffer))

	destroy_video_decoder(video_codec, video_decoder)

	assert decode_video_frame(video_codec, video_decoder, encode_buffer) is None


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8', 'vp9' ])
def test_create_and_destroy_video_encoder(video_codec : VideoCodec) -> None:
	video_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	input_buffer = cv2.cvtColor(video_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	video_encoder = create_video_encoder(video_codec, (426, 226), 4000)

	if video_codec == 'av1':
		assert aom_encoder.encode(video_encoder, input_buffer, (426, 226), 0)
	if video_codec in [ 'vp8', 'vp9' ]:
		assert vpx_encoder.encode(video_encoder, input_buffer, (426, 226), 0)

	destroy_video_encoder(video_codec, video_encoder)

	if video_codec == 'av1':
		assert aom_encoder.encode(video_encoder, input_buffer, (426, 226), 1) == bytes()
	if video_codec in [ 'vp8', 'vp9' ]:
		assert vpx_encoder.encode(video_encoder, input_buffer, (426, 226), 1) == bytes()


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8', 'vp9' ])
def test_update_video_encoder_resolution(video_codec : VideoCodec) -> None:
	video_encoder = create_video_encoder(video_codec, (426, 226), 4000)

	if video_codec == 'av1':
		assert struct.unpack_from('I', video_encoder, 128 + 12)[0] == 426

	if video_codec == 'vp8':
		assert struct.unpack_from('I', video_encoder, 64 + 12)[0] == 426

	if video_codec == 'vp9':
		assert struct.unpack_from('I', video_encoder, 64 + 12)[0] == 426

	assert update_video_encoder_resolution(video_codec, video_encoder, (320, 180))

	if video_codec == 'av1':
		assert struct.unpack_from('I', video_encoder, 128 + 12)[0] == 320

	if video_codec == 'vp8':
		assert struct.unpack_from('I', video_encoder, 64 + 12)[0] == 320

	if video_codec == 'vp9':
		assert struct.unpack_from('I', video_encoder, 64 + 12)[0] == 320

	destroy_video_encoder(video_codec, video_encoder)


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8', 'vp9' ])
def test_update_video_encoder_bitrate(video_codec : VideoCodec) -> None:
	video_encoder = create_video_encoder(video_codec, (426, 226), 4000)

	if video_codec == 'av1':
		assert struct.unpack_from('I', video_encoder, 128 + 136)[0] == 4000

	if video_codec == 'vp8':
		assert struct.unpack_from('I', video_encoder, 64 + 112)[0] == 4000

	if video_codec == 'vp9':
		assert struct.unpack_from('I', video_encoder, 64 + 112)[0] == 4000

	assert update_video_encoder_bitrate(video_codec, video_encoder, 6000)

	if video_codec == 'av1':
		assert struct.unpack_from('I', video_encoder, 128 + 136)[0] == 6000

	if video_codec == 'vp8':
		assert struct.unpack_from('I', video_encoder, 64 + 112)[0] == 6000

	if video_codec == 'vp9':
		assert struct.unpack_from('I', video_encoder, 64 + 112)[0] == 6000

	destroy_video_encoder(video_codec, video_encoder)


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8', 'vp9' ])
def test_handle_video_frame(video_codec : VideoCodec) -> None:
	video_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_decoder = create_video_decoder(video_codec)
	video_queue : Queue[Tuple[Time, Future[BufferPack]]] = Queue(maxsize = 30)

	with ThreadPoolExecutor(max_workers = 1) as executor:
		with patch('facefusion.apis.stream_video.decode_video_frame', return_value = video_frame):
			with patch('facefusion.apis.stream_video.process_video_frame', return_value = BufferPack(buffer = video_frame.tobytes(), resolution = (426, 226))):
				handle_video_frame(video_codec, video_decoder, video_queue, executor, 0, ctypes.c_void_p(), 1, ctypes.c_void_p(), ctypes.c_void_p())
				_, video_future = video_queue.get_nowait()

	video_buffer = video_future.result().get('buffer')

	if is_linux() or is_windows():
		assert create_hash(video_buffer) == 'a17439db'

	if is_macos():
		assert create_hash(video_buffer) == '38d00e2a'
