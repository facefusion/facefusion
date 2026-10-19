import ctypes
import ctypes.util
from functools import lru_cache
from typing import Callable, List, Optional


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


def lookup_method(interface_handle : ctypes.c_void_p, method_index : int, restype : type, argtypes : List[type]) -> Callable[..., int]:
	method_table = ctypes.cast(interface_handle, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
	return ctypes.WINFUNCTYPE(restype, *argtypes)(method_table[method_index])  # type: ignore[attr-defined]


def define_device_memory() -> ctypes.Structure:
	return type('ADLX_GPU_MEMORY', (ctypes.Structure,),
	{
		'_fields_':
		[
			('memory_total', ctypes.c_uint32),
			('memory_used', ctypes.c_int32)
		]
	})()
