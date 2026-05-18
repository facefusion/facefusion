from unittest.mock import patch

import cv2
import pytest
from tests.assert_helper import get_test_example_file, get_test_examples_directory

from facefusion import state_manager
from facefusion.codecs.aom_decoder import create_aom_decoder, decode, destroy_aom_decoder, read_aom_resolution
from facefusion.codecs.aom_encoder import create_aom_encoder, encode
from facefusion.download import conditional_download
from facefusion.libraries import aom as aom_module
from facefusion.vision import read_video_frame


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])

	conditional_download(get_test_examples_directory(), [ 'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4' ])

	aom_module.pre_check()


#TODO: needs review
def test_create_aom_decoder() -> None:
	assert create_aom_decoder()


#TODO: needs review
def test_decode() -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_buffer = cv2.cvtColor(vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	video_resolution = (vision_frame.shape[1], vision_frame.shape[0])
	aom_encoder = create_aom_encoder(video_resolution, 1000, 1, 0)
	encoded_buffer = encode(aom_encoder, video_buffer, video_resolution, 0)
	decode_resolution = read_aom_resolution(create_aom_decoder(), encoded_buffer)

	assert len(decode(create_aom_decoder(), encoded_buffer)) == decode_resolution[0] * decode_resolution[1] * 3 // 2
	assert decode(create_aom_decoder(), bytes()) == bytes()


#TODO: needs review
def test_read_aom_resolution() -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_buffer = cv2.cvtColor(vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	video_resolution = (vision_frame.shape[1], vision_frame.shape[0])
	aom_encoder = create_aom_encoder(video_resolution, 1000, 1, 0)
	encoded_buffer = encode(aom_encoder, video_buffer, video_resolution, 0)

	assert read_aom_resolution(create_aom_decoder(), encoded_buffer)[0] >= video_resolution[0]
	assert read_aom_resolution(create_aom_decoder(), encoded_buffer)[1] >= video_resolution[1]
	assert read_aom_resolution(create_aom_decoder(), bytes()) is None


#TODO: needs review
def test_destroy_aom_decoder() -> None:
	aom_decoder = create_aom_decoder()

	with patch.object(aom_module.create_static_library(), 'aom_codec_destroy') as mock:
		destroy_aom_decoder(aom_decoder)
		mock.assert_called_once_with(aom_decoder)
