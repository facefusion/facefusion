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
from facefusion.types import AudioCodec, AudioFrame, Buffer, FrameHandler, RtcPeer, RtcPeerAudio
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


def dispatch_frame(buffer : Buffer, track : int, frame_handler : FrameHandler) -> threading.Event:
	frame_handler(buffer, 0)
	ready_event = threading.Event()
	ready_event.set()
	return ready_event


def test_run_audio_encode_loop() -> None:
	audio_buffer = read_audio_buffer(get_test_example_file('source.mp3'), 48000, 16, 2)
	audio_frame = numpy.frombuffer(audio_buffer, dtype = numpy.int16).astype(numpy.float32) / 32768.0
	peer_connection = rtc.create_peer_connection()
	rtc_peer : RtcPeer =\
	{
		'peer_connection': peer_connection,
		'audio':
		{
			'sender_track': 0,
			'receiver_track': 0,
			'codec': 'opus'
		},
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

	with patch('facefusion.apis.stream_audio.create_receive_event', side_effect = partial(dispatch_frame, bytes([ 0 ]))):
		with patch('facefusion.apis.stream_audio.decode_audio_frame', return_value = audio_frame.tobytes()):
			rtc_peer_audio : RtcPeerAudio =\
			{
				'sender_track': 0,
				'receiver_track': 0,
				'codec': audio_codec
			}
			receive_audio_frames(rtc_peer_audio, audio_queue)

	_, temp_audio_frame = audio_queue.get_nowait()

	assert create_hash(temp_audio_frame.tobytes()) == create_hash(audio_frame.tobytes())


def test_handle_audio_frame() -> None:
	audio_buffer = read_audio_buffer(get_test_example_file('source.mp3'), 48000, 16, 2)
	audio_frame = numpy.frombuffer(audio_buffer, dtype = numpy.int16).astype(numpy.float32) / 32768.0
	audio_decoder_mock = MagicMock()
	audio_queue : Queue[Tuple[float, AudioFrame]] = Queue(maxsize = 300)

	with patch('facefusion.apis.stream_audio.decode_audio_frame', return_value = audio_frame.tobytes()):
		handle_audio_frame('opus', audio_decoder_mock, audio_queue, bytes(), 0)

	_, temp_audio_frame = audio_queue.get_nowait()

	assert create_hash(temp_audio_frame.tobytes()) == create_hash(audio_frame.tobytes())
