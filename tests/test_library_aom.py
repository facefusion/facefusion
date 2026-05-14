import ctypes

import pytest

from facefusion import state_manager
from facefusion.libraries import aom as aom_module


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])

	aom_module.pre_check()


def test_create_static_library() -> None:
	assert isinstance(aom_module.create_static_library(), ctypes.CDLL)
