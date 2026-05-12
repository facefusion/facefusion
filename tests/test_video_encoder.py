from unittest.mock import patch

import cv2
import pytest
from tests.assert_helper import get_test_example_file, get_test_examples_directory

from facefusion import state_manager
from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download
from facefusion.hash_helper import create_hash
from facefusion.libraries import vpx as vpx_module
from facefusion.video_encoder import create_vpx_encoder, destroy_vpx_encoder, encode_vpx_buffer
from facefusion.vision import read_video_frame


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])

	conditional_download(get_test_examples_directory(), [ 'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4' ])

	vpx_module.pre_check()


def test_create_vpx_encoder() -> None:
	assert create_vpx_encoder(320, 240, 1000, 8, 16)
	assert create_vpx_encoder(0, 0, 0, 0, 0) is None


def test_encode_vpx_buffer() -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	height, width = vision_frame.shape[:2]
	vpx_encoder = create_vpx_encoder(width, height, 1000, 1, 0)

	buffer_valid = cv2.cvtColor(vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	buffer_invalid = bytes(0)

	if is_linux() or is_windows():
		assert create_hash(encode_vpx_buffer(vpx_encoder, buffer_valid, width, height, 3, 1)) == 'ce133a1f'

	if is_macos():
		assert create_hash(encode_vpx_buffer(vpx_encoder, buffer_valid, width, height, 3, 1)) == '21c36925'

	assert encode_vpx_buffer(vpx_encoder, buffer_invalid, width, height, 0, 0) == b''


def test_destroy_vpx_encoder() -> None:
	vpx_encoder = create_vpx_encoder(320, 240, 1000, 8, 16)

	with patch.object(vpx_module.create_static_library(), 'vpx_codec_destroy') as mock:
		destroy_vpx_encoder(vpx_encoder)
		mock.assert_called_once_with(vpx_encoder)
