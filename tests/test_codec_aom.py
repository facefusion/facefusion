from unittest.mock import patch

import cv2
import pytest
from tests.assert_helper import get_test_example_file, get_test_examples_directory

from facefusion import state_manager
from facefusion.codecs.aom import create_aom_encoder, destroy_aom_encoder, encode_aom_buffer
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


def test_create_aom_encoder() -> None:
	assert create_aom_encoder((320, 240), 1000, 8, 16)
	assert create_aom_encoder((0, 0), 0, 0, 0) is None


def test_encode_aom_buffer() -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_buffer = cv2.cvtColor(vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	video_resolution = (vision_frame.shape[1], vision_frame.shape[0])
	aom_encoder = create_aom_encoder(video_resolution, 1000, 1, 0)

	if is_linux() or is_windows():
		assert create_hash(encode_aom_buffer(aom_encoder, video_buffer, video_resolution, 3)) == '3ab6cc31'

	if is_macos():
		assert create_hash(encode_aom_buffer(aom_encoder, video_buffer, video_resolution, 3)) == '8ecd1108'


def test_destroy_aom_encoder() -> None:
	aom_encoder = create_aom_encoder((320, 240), 1000, 8, 16)

	with patch.object(aom_module.create_static_library(), 'aom_codec_destroy') as mock:
		destroy_aom_encoder(aom_encoder)
		mock.assert_called_once_with(aom_encoder)
