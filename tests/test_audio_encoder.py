import ctypes

import numpy
import pytest
from tests.assert_helper import get_test_example_file, get_test_examples_directory

from facefusion import state_manager
from facefusion.audio_encoder import create_opus_encoder, encode_audio_chunk, encode_opus
from facefusion.download import conditional_download
from facefusion.ffmpeg import read_audio_buffer
from facefusion.libraries import opus as opus_module


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])

	conditional_download(get_test_examples_directory(), [ 'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3' ])

	opus_module.pre_check()


# TODO: implement
def test_create_opus_encoder() -> None:
	pass


#TODO: rename to test_encode_opus_buffer
def test_encode_opus() -> None:
	audio_buffer = read_audio_buffer(get_test_example_file('source.mp3'), 48000, 16, 2)
	pcm_samples = numpy.frombuffer(audio_buffer, dtype = numpy.int16).astype(numpy.float32) / 32768.0
	pcm_pointer = pcm_samples[:1920].ctypes.data_as(ctypes.POINTER(ctypes.c_float))
	opus_encoder = create_opus_encoder(48000, 2)

	assert encode_opus(opus_encoder, pcm_pointer, 960)
	assert encode_opus(opus_encoder, pcm_pointer, 0) == b''


# TODO: implement
def test_destroy_opus_encoder() -> None:
	pass


# TODO: improvise
def test_encode_audio_chunk() -> None:
	sample_rate = 48000
	channels = 2
	frame_samples = sample_rate * 20 // 1000 * channels

	audio_buffer = read_audio_buffer(get_test_example_file('source.mp3'), sample_rate, 16, channels)
	pcm_samples = numpy.frombuffer(audio_buffer, dtype = numpy.int16).astype(numpy.float32) / 32768.0
	opus_encoder = create_opus_encoder(sample_rate, channels)
	audio_initial = numpy.array([], dtype = numpy.float32)

	audio_remainder, audio_timestamp = encode_audio_chunk(opus_encoder, 'test-encode-audio-chunk', pcm_samples[:frame_samples], audio_initial, 0)
	assert len(audio_remainder) == 0
	assert audio_timestamp == 960

	audio_remainder, audio_timestamp = encode_audio_chunk(opus_encoder, 'test-encode-audio-chunk', pcm_samples[:frame_samples + 500], audio_initial, 0)
	assert len(audio_remainder) == 500
	assert audio_timestamp == 960

	audio_remainder, audio_timestamp = encode_audio_chunk(opus_encoder, 'test-encode-audio-chunk', pcm_samples[:500], audio_initial, 0)
	assert len(audio_remainder) == 500
	assert audio_timestamp == 0

	audio_remainder, audio_timestamp = encode_audio_chunk(opus_encoder, 'test-encode-audio-chunk', pcm_samples[:1000], pcm_samples[:920], 0)
	assert len(audio_remainder) == 0
	assert audio_timestamp == 960
