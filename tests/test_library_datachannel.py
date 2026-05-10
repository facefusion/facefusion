import ctypes

import pytest

from facefusion import state_manager
from facefusion.common_helper import is_windows
from facefusion.libraries import datachannel as datachannel_module


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])
	datachannel_module.pre_check()


# TODO: add support for Windows
@pytest.mark.skipif(is_windows(), reason = 'not supported on Windows')
def test_create_static_library() -> None:
	assert isinstance(datachannel_module.create_static_library(), ctypes.CDLL)
