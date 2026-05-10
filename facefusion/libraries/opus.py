import ctypes
import ctypes.util
from functools import lru_cache
from typing import Optional


@lru_cache
def create_static_library() -> Optional[ctypes.CDLL]:
	library_path = ctypes.util.find_library('opus') or ctypes.util.find_library('libopus')

	if library_path:
		library = ctypes.CDLL(library_path)

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
