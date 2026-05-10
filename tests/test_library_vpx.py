import ctypes

import pytest

from facefusion.common_helper import is_windows
from facefusion.libraries import vpx as vpx_module


# TODO: add support for Windows
@pytest.mark.skipif(is_windows(), reason = 'not supported on Windows')
def test_create_static_library() -> None:
	assert isinstance(vpx_module.create_static_library(), ctypes.CDLL)


# TODO: add support for Windows
@pytest.mark.skipif(is_windows(), reason = 'not supported on Windows')
def test_create_vpx_encoder() -> None:
	vpx_library = vpx_module.create_static_library()

	assert isinstance(vpx_library, ctypes.CDLL)
