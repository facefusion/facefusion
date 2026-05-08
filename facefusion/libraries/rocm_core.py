import ctypes
from functools import lru_cache
from typing import Optional

from facefusion.common_helper import is_linux


def resolve_library_file() -> Optional[str]:
	if is_linux():
		return 'librocm-core.so'
	return None


@lru_cache
def create_static_library() -> Optional[ctypes.CDLL]:
	library_file = resolve_library_file()

	if library_file:
		rocm_core_library = ctypes.CDLL(library_file)
		return init_ctypes(rocm_core_library)

	return None


def init_ctypes(rocm_core : ctypes.CDLL) -> ctypes.CDLL:
	rocm_core.getROCmVersion.argtypes = [ ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint) ]
	rocm_core.getROCmVersion.restype = ctypes.c_int

	return rocm_core
