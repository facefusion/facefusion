import ctypes

from facefusion.libraries import datachannel as datachannel_module


def test_create_static_library() -> None:
	assert isinstance(datachannel_module.create_static_library(), ctypes.CDLL)
