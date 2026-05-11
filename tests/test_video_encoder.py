import cv2
import pytest
from tests.assert_helper import get_test_example_file, get_test_examples_directory

from facefusion import state_manager
from facefusion.download import conditional_download
from facefusion.libraries import vpx as vpx_module
from facefusion.video_encoder import create_vpx_encoder, encode_vpx
from facefusion.vision import read_video_frame


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])
	conditional_download(get_test_examples_directory(), [ 'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4' ])

	vpx_module.pre_check()


def test_encode_vpx() -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	height, width = vision_frame.shape[:2]
	buffer_valid = cv2.cvtColor(vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	buffer_invalid = bytes(0)
	vpx_encoder = create_vpx_encoder(width, height, 1000)

	assert encode_vpx(vpx_encoder, buffer_valid, width, height, 3, 1)
	assert encode_vpx(vpx_encoder, buffer_invalid, width, height, 0, 0) == b''
