import ctypes

import pytest

from facefusion.common_helper import is_windows
from facefusion.libraries import opus as opus_module


# TODO: add support for Windows
@pytest.mark.skipif(is_windows(), reason = 'not supported on Windows')
def test_create_static_library() -> None:
	assert isinstance(opus_module.create_static_library(), ctypes.CDLL)


# TODO: add support for Windows
@pytest.mark.skipif(is_windows(), reason = 'not supported on Windows')
def test_create_opus_encoder() -> None:
	opus_library = opus_module.create_static_library()

	assert isinstance(opus_library, ctypes.CDLL)
