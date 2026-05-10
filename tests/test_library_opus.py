import ctypes

import pytest

from facefusion import environment
from facefusion.libraries import opus as opus_module


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	environment.setup_for_system()


def test_create_static_library() -> None:
	assert isinstance(opus_module.create_static_library(), ctypes.CDLL)


def test_create_opus_encoder() -> None:
	opus_library = opus_module.create_static_library()

	assert isinstance(opus_library, ctypes.CDLL)
