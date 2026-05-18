from unittest.mock import patch

import cv2
import pytest
from tests.assert_helper import get_test_example_file, get_test_examples_directory

from facefusion import state_manager
from facefusion.codecs.vpx_decoder import create, decode, destroy, read_resolution
from facefusion.codecs.vpx_encoder import create as create_encoder, encode
from facefusion.download import conditional_download
from facefusion.libraries import vpx as vpx_module
from facefusion.vision import read_video_frame


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])

	conditional_download(get_test_examples_directory(), [ 'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4' ])

	vpx_module.pre_check()


#TODO: needs review
def test_create() -> None:
	assert create()


#TODO: needs review
def test_decode() -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_buffer = cv2.cvtColor(vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	video_resolution = (vision_frame.shape[1], vision_frame.shape[0])
	vpx_encoder = create_encoder(video_resolution, 1000, 1, 0)
	encoded_buffer = encode(vpx_encoder, video_buffer, video_resolution, 0)
	vpx_decoder = create()

	assert len(decode(vpx_decoder, encoded_buffer)) == video_resolution[0] * video_resolution[1] * 3 // 2
	assert decode(vpx_decoder, bytes()) == bytes()


#TODO: needs review
def test_read_resolution() -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_buffer = cv2.cvtColor(vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	video_resolution = (vision_frame.shape[1], vision_frame.shape[0])
	vpx_encoder = create_encoder(video_resolution, 1000, 1, 0)
	encoded_buffer = encode(vpx_encoder, video_buffer, video_resolution, 0)
	vpx_decoder = create()

	assert read_resolution(vpx_decoder, encoded_buffer) == video_resolution
	assert read_resolution(vpx_decoder, bytes()) is None


#TODO: needs review
def test_destroy() -> None:
	vpx_decoder = create()

	with patch.object(vpx_module.create_static_library(), 'vpx_codec_destroy') as mock:
		destroy(vpx_decoder)
		mock.assert_called_once_with(vpx_decoder)
