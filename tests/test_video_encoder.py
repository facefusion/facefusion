import pytest

from facefusion import state_manager
from facefusion.libraries import vpx as vpx_module
from facefusion.video_encoder import create_vpx_encoder, encode_vpx


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])

	vpx_module.pre_check()


def test_encode_vpx() -> None:
	codec_context = create_vpx_encoder(320, 240, 1000)
	yuv_buffer = bytes(320 * 240 * 3 // 2)
	invalid_yuv_buffer = bytes(640 * 480 * 3 // 2)

	assert isinstance(encode_vpx(codec_context, yuv_buffer, 320, 240, 0, 0), bytes)
	assert isinstance(encode_vpx(codec_context, yuv_buffer, 320, 240, 2, 0), bytes)
	assert encode_vpx(codec_context, yuv_buffer, 320, 240, 1, 0)[0] & 1 == 1
	assert encode_vpx(codec_context, yuv_buffer, 320, 240, 3, 1)[3:].startswith(b'\x9d\x01\x2a')
	assert encode_vpx(codec_context, invalid_yuv_buffer, 640, 480, 0, 0) == b''
