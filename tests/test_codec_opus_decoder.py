from unittest.mock import patch

import numpy
import pytest
from tests.assert_helper import get_test_example_file, get_test_examples_directory

from facefusion import state_manager
from facefusion.codecs.opus_decoder import create, decode, destroy
from facefusion.codecs.opus_encoder import create as create_encoder, encode
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


def test_create() -> None:
	assert create(48000, 2)

	with patch('facefusion.codecs.opus_decoder.opus_module.create_static_library', return_value = None):
		assert create(48000, 2) is None


def test_decode() -> None:
	audio_buffer = read_audio_buffer(get_test_example_file('source.mp3'), 48000, 16, 2)
	audio_sample = numpy.frombuffer(audio_buffer, dtype = numpy.int16).astype(numpy.float32) / 32768.0
	opus_encoder = create_encoder(48000, 2)
	encoded_buffer = encode(opus_encoder, audio_sample.tobytes(), 960)
	opus_decoder = create(48000, 2)

	if is_linux() or is_windows():
		assert create_hash(decode(opus_decoder, encoded_buffer, 960, 2)) == 'cadd63d1'

	if is_macos():
		assert create_hash(decode(opus_decoder, encoded_buffer, 960, 2)) == '92f7997d'


def test_destroy() -> None:
	opus_decoder = create(48000, 2)

	with patch.object(opus_module.create_static_library(), 'opus_decoder_destroy') as mock:
		destroy(opus_decoder)
		mock.assert_called_once_with(opus_decoder)
