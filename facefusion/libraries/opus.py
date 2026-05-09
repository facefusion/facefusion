import ctypes
from functools import lru_cache
from typing import Optional

from facefusion.common_helper import is_linux, is_macos, is_windows


def resolve_library_file() -> Optional[str]:
	if is_linux():
		return 'libopus.so.0'
	if is_macos():
		return 'libopus.dylib'
	if is_windows():
		return 'opus.dll'
	return None


@lru_cache
def create_static_library() -> Optional[ctypes.CDLL]:
	library_file = resolve_library_file()

	if library_file:
		library = ctypes.CDLL(library_file)

		if library:
			return init_ctypes(library)

	return None


def init_ctypes(library : ctypes.CDLL) -> ctypes.CDLL:
	library.opus_encoder_create.argtypes = [ ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int) ]
	library.opus_encoder_create.restype = ctypes.c_void_p

	library.opus_encode_float.argtypes = [ ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int ]
	library.opus_encode_float.restype = ctypes.c_int

	library.opus_encoder_destroy.argtypes = [ ctypes.c_void_p ]
	library.opus_encoder_destroy.restype = None

	library.opus_encoder_ctl.argtypes = [ ctypes.c_void_p, ctypes.c_int, ctypes.c_int ]
	library.opus_encoder_ctl.restype = ctypes.c_int

	return library
