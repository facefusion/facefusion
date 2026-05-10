import ctypes

import pytest

from facefusion import state_manager
from facefusion.libraries import vpx as vpx_module


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])
	vpx_module.pre_check()


def test_create_static_library() -> None:
	assert isinstance(vpx_module.create_static_library(), ctypes.CDLL)


def test_create_vpx_encoder() -> None:
	vpx_library = vpx_module.create_static_library()

	assert isinstance(vpx_library, ctypes.CDLL)
