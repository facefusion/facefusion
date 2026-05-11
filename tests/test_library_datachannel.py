import ctypes

import pytest

from facefusion import state_manager
from facefusion.libraries import datachannel as datachannel_module


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])

	datachannel_module.pre_check()


def test_create_static_library() -> None:
	assert isinstance(datachannel_module.create_static_library(), ctypes.CDLL)
