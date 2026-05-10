import ctypes

import pytest

from facefusion import environment
from facefusion.libraries import vpx as vpx_module


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	environment.setup()


def test_create_static_library() -> None:
	assert isinstance(vpx_module.create_static_library(), ctypes.CDLL)


def test_create_vpx_encoder() -> None:
	vpx_library = vpx_module.create_static_library()

	assert isinstance(vpx_library, ctypes.CDLL)
