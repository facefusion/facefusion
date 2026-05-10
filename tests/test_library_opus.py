import ctypes

from facefusion.libraries import opus as opus_module


def test_create_static_library() -> None:
	assert isinstance(opus_module.create_static_library(), ctypes.CDLL)


def test_create_opus_encoder() -> None:
	opus_library = opus_module.create_static_library()

	assert isinstance(opus_library, ctypes.CDLL)
