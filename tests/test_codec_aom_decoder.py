from unittest.mock import patch

import cv2
import pytest
from tests.assert_helper import get_test_example_file, get_test_examples_directory

from facefusion import state_manager
from facefusion.codecs.aom_decoder import create, decode, destroy
from facefusion.codecs.aom_encoder import create as create_encoder, encode
from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download
from facefusion.hash_helper import create_hash
from facefusion.libraries import aom as aom_module
from facefusion.vision import read_video_frame


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])

	conditional_download(get_test_examples_directory(), [ 'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4' ])

	aom_module.pre_check()


def test_create() -> None:
	assert create(1)

	with patch('facefusion.libraries.aom.create_static_library', return_value = None):
		assert create(1) is None


def test_decode() -> None:
	video_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_buffer = cv2.cvtColor(video_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	video_resolution = (video_frame.shape[1], video_frame.shape[0])
	aom_encoder = create_encoder(video_resolution, 1000, 1, 0)
	encode_buffer = encode(aom_encoder, video_buffer, video_resolution, 0)
	aom_decoder = create(1)

	if is_linux() or is_windows():
		assert create_hash(decode(aom_decoder, encode_buffer).get('buffer')) == 'e3c0ebd8'

	if is_macos():
		assert create_hash(decode(aom_decoder, encode_buffer).get('buffer')) == 'c8c6fdaa'


def test_destroy() -> None:
	aom_decoder = create(1)

	with patch.object(aom_module.create_static_library(), 'aom_codec_destroy') as mock:
		destroy(aom_decoder)
		mock.assert_called_once_with(aom_decoder)
