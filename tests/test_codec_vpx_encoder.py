from unittest.mock import patch

import cv2
import pytest
from tests.assert_helper import get_test_example_file, get_test_examples_directory

from facefusion import state_manager
from facefusion.codecs.vpx_encoder import create, destroy, encode
from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download
from facefusion.hash_helper import create_hash
from facefusion.libraries import vpx as vpx_module
from facefusion.types import VxpVideoCodec
from facefusion.vision import read_video_frame


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])

	conditional_download(get_test_examples_directory(), [ 'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4' ])

	vpx_module.pre_check()


@pytest.mark.parametrize('video_codec', [ 'vp8', 'vp9' ])
def test_create(video_codec : VxpVideoCodec) -> None:
	assert create(video_codec, (320, 240), 1000, 8, 16)

	with patch('facefusion.libraries.vpx.create_static_library', return_value = None):
		assert create(video_codec, (320, 240), 1000, 8, 16) is None


@pytest.mark.parametrize('video_codec', [ 'vp8', 'vp9' ])
def test_encode(video_codec : VxpVideoCodec) -> None:
	video_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_buffer = cv2.cvtColor(video_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	video_resolution = (video_frame.shape[1], video_frame.shape[0])
	vpx_encoder = create(video_codec, video_resolution, 1000, 1, 0)

	if is_linux() or is_windows():
		if video_codec == 'vp8':
			assert create_hash(encode(vpx_encoder, video_buffer, video_resolution, 3)) == 'ce133a1f'

		if video_codec == 'vp9':
			assert create_hash(encode(vpx_encoder, video_buffer, video_resolution, 3)) == 'b0760d5e'

	if is_macos():
		pytest.skip()


@pytest.mark.parametrize('video_codec', [ 'vp8', 'vp9' ])
def test_destroy(video_codec : VxpVideoCodec) -> None:
	vpx_encoder = create(video_codec, (320, 240), 1000, 8, 16)

	with patch.object(vpx_module.create_static_library(), 'vpx_codec_destroy') as mock:
		destroy(vpx_encoder)
		mock.assert_called_once_with(vpx_encoder)
