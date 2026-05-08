import ctypes
from functools import lru_cache
from typing import Optional

from facefusion.common_helper import is_linux, is_windows


def resolve_library_file() -> Optional[str]:
	if is_linux():
		return 'libnvidia-ml.so.1'
	if is_windows():
		return 'nvml.dll'
	return None


@lru_cache
def create_static_nvml_library() -> Optional[ctypes.CDLL]:
	library_file = resolve_library_file()

	if library_file:
		nvml_library = ctypes.CDLL(library_file)
		return init_ctypes(nvml_library)

	return None


def create_nvml_memory() -> ctypes.Structure:
	return type('NVML_MEMORY', (ctypes.Structure,),
	{
		'_fields_':
		[
			('total', ctypes.c_ulonglong),
			('free', ctypes.c_ulonglong),
			('used', ctypes.c_ulonglong)
		]
	})()


def create_nvml_utilization() -> ctypes.Structure:
	return type('NVML_UTILIZATION', (ctypes.Structure,),
	{
		'_fields_':
		[
			('gpu', ctypes.c_uint),
			('memory', ctypes.c_uint)
		]
	})()


def init_ctypes(nvml_library : ctypes.CDLL) -> ctypes.CDLL:
	nvml_library.nvmlInit_v2.argtypes = []
	nvml_library.nvmlInit_v2.restype = ctypes.c_int

	nvml_library.nvmlShutdown.argtypes = []
	nvml_library.nvmlShutdown.restype = ctypes.c_int

	nvml_library.nvmlDeviceGetCount_v2.argtypes = [ ctypes.POINTER(ctypes.c_uint) ]
	nvml_library.nvmlDeviceGetCount_v2.restype = ctypes.c_int

	nvml_library.nvmlSystemGetDriverVersion.argtypes = [ ctypes.c_char_p, ctypes.c_uint ]
	nvml_library.nvmlSystemGetDriverVersion.restype = ctypes.c_int

	nvml_library.nvmlSystemGetCudaDriverVersion.argtypes = [ ctypes.POINTER(ctypes.c_int) ]
	nvml_library.nvmlSystemGetCudaDriverVersion.restype = ctypes.c_int

	nvml_library.nvmlDeviceGetHandleByIndex_v2.argtypes = [ ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p) ]
	nvml_library.nvmlDeviceGetHandleByIndex_v2.restype = ctypes.c_int

	nvml_library.nvmlDeviceGetName.argtypes = [ ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint ]
	nvml_library.nvmlDeviceGetName.restype = ctypes.c_int

	nvml_library.nvmlDeviceGetMemoryInfo.argtypes = [ ctypes.c_void_p, ctypes.c_void_p ]
	nvml_library.nvmlDeviceGetMemoryInfo.restype = ctypes.c_int

	nvml_library.nvmlDeviceGetTemperature.argtypes = [ ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_uint) ]
	nvml_library.nvmlDeviceGetTemperature.restype = ctypes.c_int

	nvml_library.nvmlDeviceGetUtilizationRates.argtypes = [ ctypes.c_void_p, ctypes.c_void_p ]
	nvml_library.nvmlDeviceGetUtilizationRates.restype = ctypes.c_int

	return nvml_library
