import ctypes
import ctypes.util
from functools import lru_cache
from typing import Optional


@lru_cache
def create_static_library() -> Optional[ctypes.CDLL]:
	library_path = ctypes.util.find_library('amdadlx64')

	if library_path:
		library = ctypes.CDLL(library_path)

		if library:
			return init_ctypes(library)

	return None


def init_ctypes(library : ctypes.CDLL) -> ctypes.CDLL:
	library.ADLXQueryFullVersion.argtypes = [ ctypes.POINTER(ctypes.c_uint64) ]
	library.ADLXQueryFullVersion.restype = ctypes.c_int

	library.ADLXQueryVersion.argtypes = [ ctypes.POINTER(ctypes.c_char_p) ]
	library.ADLXQueryVersion.restype = ctypes.c_int

	library.ADLXInitialize.argtypes = [ ctypes.c_uint64, ctypes.POINTER(ctypes.c_void_p) ]
	library.ADLXInitialize.restype = ctypes.c_int

	library.ADLXTerminate.argtypes = []
	library.ADLXTerminate.restype = ctypes.c_int

	return library


def define_product_info() -> ctypes.Structure:
	return type('ADLX_PRODUCT_INFO', (ctypes.Structure,),
	{
		'_fields_':
		[
			('name', ctypes.c_char_p),
			('vram_total_mb', ctypes.c_uint32)
		]
	})()


def define_device_metrics() -> ctypes.Structure:
	return type('ADLX_GPU_METRICS', (ctypes.Structure,),
	{
		'_fields_':
		[
			('vram_used_mb', ctypes.c_int32),
			('temperature', ctypes.c_double),
			('utilization', ctypes.c_double)
		]
	})()
