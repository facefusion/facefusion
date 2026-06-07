import ctypes
import threading
from functools import partial
from queue import Queue
from typing import Tuple
from unittest.mock import MagicMock, patch

import numpy
import pytest

from facefusion import rtc, rtc_store, state_manager
from facefusion.apis.stream_audio import handle_audio_frame, receive_audio_frames, run_audio_encode_loop
from facefusion.download import conditional_download
from facefusion.ffmpeg import read_audio_buffer
from facefusion.hash_helper import create_hash
from facefusion.libraries import datachannel as datachannel_module, opus as opus_module
from facefusion.types import AudioCodec, AudioFrame, FrameHandler, RtcPeer, RtcPeerAudio
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])
	state_manager.init_item('processors', [])

	opus_module.pre_check()
	datachannel_module.pre_check()

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3'
	])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	rtc_store.clear()


def set_ready_event(ready_event : threading.Event, track : int, close_callback : FrameHandler) -> None:
	ready_event.set()


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

	audio_queue : Queue[Tuple[float, AudioFrame]] = Queue(maxsize = 300)

	audio_queue.put((0.100, audio_frame))

	encoder_mock = MagicMock()
	encoder_mock.encode.return_value = bytes([ 1 ] * 32)

	with patch('facefusion.apis.stream_audio.opus_encoder.encode', encoder_mock.encode):
		with patch('facefusion.apis.stream_audio.rtc.send_audio') as send_audio_mock:
			audio_loop_thread = threading.Thread(target = run_audio_encode_loop, args = (rtc_peer, audio_queue), daemon = True)
			audio_loop_thread.start()
			audio_queue.put((0.0, numpy.empty(0)))
			audio_loop_thread.join(timeout = 5.0)

	assert encoder_mock.encode.called is True
	assert send_audio_mock.called is True


@pytest.mark.parametrize('audio_codec', [ 'opus' ])
def test_receive_audio_frames(audio_codec : AudioCodec) -> None:
	audio_buffer = read_audio_buffer(get_test_example_file('source.mp3'), 48000, 16, 2)
	audio_frame = numpy.frombuffer(audio_buffer, dtype = numpy.int16).astype(numpy.float32) / 32768.0
	audio_queue : Queue[Tuple[float, AudioFrame]] = Queue(maxsize = 300)

	datachannel_mock = MagicMock()
	ready_event = threading.Event()
	datachannel_mock.rtcSetClosedCallback.side_effect = partial(set_ready_event, ready_event)

	with patch('facefusion.libraries.datachannel.create_static_library', return_value = datachannel_mock):
		with patch('facefusion.apis.stream_audio.decode_audio_frame', return_value = audio_frame.tobytes()):
			rtc_peer_audio : RtcPeerAudio =\
			{
				'sender_track': 0,
				'receiver_track': 0,
				'codec': audio_codec
			}
			audio_receiver_thread = threading.Thread(target = receive_audio_frames, args = (rtc_peer_audio, audio_queue), daemon = True)
			audio_receiver_thread.start()
			ready_event.wait(timeout = 5.0)
			datachannel_mock.rtcSetFrameCallback.call_args[0][1](0, bytes([ 0 ]), 1, None, None)
			datachannel_mock.rtcSetClosedCallback.call_args[0][1](0, None)
			audio_receiver_thread.join(timeout = 5.0)

	# todo: buffer frame or output_buffer or output_audio_buffer? follow codebase naming
	_, buffer_frame = audio_queue.get_nowait()

	assert create_hash(buffer_frame.tobytes()) == create_hash(audio_frame.tobytes())


def test_handle_audio_frame() -> None:
	audio_buffer = read_audio_buffer(get_test_example_file('source.mp3'), 48000, 16, 2)
	audio_frame = numpy.frombuffer(audio_buffer, dtype = numpy.int16).astype(numpy.float32) / 32768.0
	audio_decoder_mock = MagicMock()
	audio_queue : Queue[Tuple[float, AudioFrame]] = Queue(maxsize = 300)

	with patch('facefusion.apis.stream_audio.decode_audio_frame', return_value = audio_frame.tobytes()):
		handle_audio_frame('opus', audio_decoder_mock, audio_queue, 0, ctypes.c_void_p(), 1, ctypes.c_void_p(), ctypes.c_void_p())

	# todo: buffer frame or output_buffer or output_audio_buffer? follow codebase naming
	_, buffer_frame = audio_queue.get_nowait()

	assert create_hash(buffer_frame.tobytes()) == create_hash(audio_frame.tobytes())
