import ctypes
import ctypes.util
from functools import lru_cache
from typing import List, Optional


@lru_cache
def create_static_library() -> Optional[ctypes.CDLL]:
	library_path = ctypes.util.find_library('nvidia-ml') or ctypes.util.find_library('nvml')

	if library_path:
		library = ctypes.CDLL(library_path)

		if library:
			return init_ctypes(library)

	return None


def init_ctypes(library : ctypes.CDLL) -> ctypes.CDLL:
	library.nvmlInit_v2.argtypes = []
	library.nvmlInit_v2.restype = ctypes.c_int

	library.nvmlShutdown.argtypes = []
	library.nvmlShutdown.restype = ctypes.c_int

	library.nvmlDeviceGetCount_v2.argtypes = [ ctypes.POINTER(ctypes.c_uint) ]
	library.nvmlDeviceGetCount_v2.restype = ctypes.c_int

	library.nvmlSystemGetDriverVersion.argtypes = [ ctypes.c_char_p, ctypes.c_uint ]
	library.nvmlSystemGetDriverVersion.restype = ctypes.c_int

	library.nvmlSystemGetCudaDriverVersion.argtypes = [ ctypes.POINTER(ctypes.c_int) ]
	library.nvmlSystemGetCudaDriverVersion.restype = ctypes.c_int

	library.nvmlDeviceGetHandleByIndex_v2.argtypes = [ ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p) ]
	library.nvmlDeviceGetHandleByIndex_v2.restype = ctypes.c_int

	library.nvmlDeviceGetName.argtypes = [ ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint ]
	library.nvmlDeviceGetName.restype = ctypes.c_int

	library.nvmlDeviceGetMemoryInfo.argtypes = [ ctypes.c_void_p, ctypes.c_void_p ]
	library.nvmlDeviceGetMemoryInfo.restype = ctypes.c_int

	library.nvmlDeviceGetTemperature.argtypes = [ ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_uint) ]
	library.nvmlDeviceGetTemperature.restype = ctypes.c_int

	library.nvmlDeviceGetUtilizationRates.argtypes = [ ctypes.c_void_p, ctypes.c_void_p ]
	library.nvmlDeviceGetUtilizationRates.restype = ctypes.c_int

	return library


def find_device_handles(nvidia_ml_library : ctypes.CDLL) -> List[ctypes.c_void_p]:
	device_handles : List[ctypes.c_void_p] = []

	device_count = ctypes.c_uint()
	nvidia_ml_library.nvmlDeviceGetCount_v2(ctypes.byref(device_count))

	for device_id in range(device_count.value):
		device_handle = ctypes.c_void_p()
		nvidia_ml_library.nvmlDeviceGetHandleByIndex_v2(device_id, ctypes.byref(device_handle))
		device_handles.append(device_handle)

	return device_handles


def define_device_memory() -> ctypes.Structure:
	return type('NVML_MEMORY', (ctypes.Structure,),
	{
		'_fields_':
		[
			('total', ctypes.c_ulonglong),
			('free', ctypes.c_ulonglong),
			('used', ctypes.c_ulonglong)
		]
	})()


def define_device_utilization() -> ctypes.Structure:
	return type('NVML_UTILIZATION', (ctypes.Structure,),
	{
		'_fields_':
		[
			('gpu', ctypes.c_uint),
			('memory', ctypes.c_uint)
		]
	})()
