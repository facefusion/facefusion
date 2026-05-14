from unittest.mock import patch

import numpy
import pytest
from tests.assert_helper import get_test_example_file, get_test_examples_directory

from facefusion import state_manager
from facefusion.codecs.opus import create_opus_encoder, destroy_opus_encoder, encode_opus_buffer
from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download
from facefusion.ffmpeg import read_audio_buffer
from facefusion.hash_helper import create_hash
from facefusion.libraries import opus as opus_module


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])

	conditional_download(get_test_examples_directory(), [ 'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3' ])

	opus_module.pre_check()


def test_create_opus_encoder() -> None:
	assert create_opus_encoder(48000, 2)
	assert create_opus_encoder(0, 0) is None


def test_encode_opus_buffer() -> None:
	audio_buffer = read_audio_buffer(get_test_example_file('source.mp3'), 48000, 16, 2)
	audio_sample = numpy.frombuffer(audio_buffer, dtype = numpy.int16).astype(numpy.float32) / 32768.0
	opus_encoder = create_opus_encoder(48000, 2)

	if is_linux() or is_windows():
		assert create_hash(encode_opus_buffer(opus_encoder, audio_sample.tobytes(), 960)) == '8abe71cf'

	if is_macos():
		assert create_hash(encode_opus_buffer(opus_encoder, audio_sample.tobytes(), 960)) == 'f595020f'


def test_destroy_opus_encoder() -> None:
	opus_encoder = create_opus_encoder(48000, 2)

	with patch.object(opus_module.create_static_library(), 'opus_encoder_destroy') as mock:
		destroy_opus_encoder(opus_encoder)
		mock.assert_called_once_with(opus_encoder)
