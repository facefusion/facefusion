import ctypes
import ctypes.util
from functools import lru_cache
from typing import Optional


@lru_cache
def create_static_library() -> Optional[ctypes.CDLL]:
	library_path = ctypes.util.find_library('vpx')

	if library_path:
		library = ctypes.CDLL(library_path)

		if library:
			return init_ctypes(library)

	return None


def init_ctypes(library : ctypes.CDLL) -> ctypes.CDLL:
	library.vpx_codec_enc_config_default.argtypes = [ ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint ]
	library.vpx_codec_enc_config_default.restype = ctypes.c_int

	library.vpx_codec_enc_init_ver.argtypes = [ ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long, ctypes.c_int ]
	library.vpx_codec_enc_init_ver.restype = ctypes.c_int

	library.vpx_codec_encode.argtypes = [ ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int64, ctypes.c_ulong, ctypes.c_long, ctypes.c_ulong ]
	library.vpx_codec_encode.restype = ctypes.c_int

	library.vpx_codec_get_cx_data.argtypes = [ ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p) ]
	library.vpx_codec_get_cx_data.restype = ctypes.c_void_p

	library.vpx_codec_destroy.argtypes = [ ctypes.c_void_p ]
	library.vpx_codec_destroy.restype = ctypes.c_int

	library.vpx_img_wrap.argtypes = [ ctypes.c_void_p, ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p ]
	library.vpx_img_wrap.restype = ctypes.c_void_p

	library.vpx_codec_control_.argtypes = [ ctypes.c_void_p, ctypes.c_int, ctypes.c_int ]
	library.vpx_codec_control_.restype = ctypes.c_int

	return library
