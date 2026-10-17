import ctypes
import ctypes.util
from functools import lru_cache
from typing import List, Optional


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


def find_device_handles(amd_adlx_library : ctypes.CDLL) -> List[ctypes.c_void_p]:
	device_handles : List[ctypes.c_void_p] = []
	device_list = ctypes.c_void_p()
	system_vtable = ctypes.cast(amd_adlx_library.system, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
	get_device_list = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))(system_vtable[1])

	if not get_device_list(amd_adlx_library.system, ctypes.byref(device_list)):
		device_list_vtable = ctypes.cast(device_list, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
		get_device_count = ctypes.WINFUNCTYPE(ctypes.c_uint32, ctypes.c_void_p)(device_list_vtable[3])
		get_device = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p))(device_list_vtable[11])

		for device_index in range(get_device_count(device_list)):
			device_handle = ctypes.c_void_p()

			if get_device(device_list, device_index, ctypes.byref(device_handle)) == 0:
				device_handles.append(device_handle)

		ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p)(device_list_vtable[1])(device_list)

	return device_handles


def get_product_info(device_handle : ctypes.c_void_p) -> ctypes.Structure:
	product_info = define_product_info()
	gpu_vtable = ctypes.cast(device_handle, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
	ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)(gpu_vtable[7])(device_handle, ctypes.byref(product_info, type(product_info).name.offset))
	ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)(gpu_vtable[11])(device_handle, ctypes.byref(product_info, type(product_info).vram_total_mb.offset))
	return product_info


def get_device_metrics(amd_adlx_library : ctypes.CDLL, device_handle : ctypes.c_void_p) -> ctypes.Structure:
	device_metrics = define_device_metrics()
	gpu_metrics = ctypes.c_void_p()

	if amd_adlx_library.performance_monitoring.value:
		performance_monitoring_vtable = ctypes.cast(amd_adlx_library.performance_monitoring, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
		ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(performance_monitoring_vtable[18])(amd_adlx_library.performance_monitoring, device_handle, ctypes.byref(gpu_metrics))

		if gpu_metrics.value:
			gpu_metrics_vtable = ctypes.cast(gpu_metrics, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
			ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)(gpu_metrics_vtable[4])(gpu_metrics, ctypes.byref(device_metrics, type(device_metrics).utilization.offset))
			ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)(gpu_metrics_vtable[7])(gpu_metrics, ctypes.byref(device_metrics, type(device_metrics).temperature.offset))
			ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)(gpu_metrics_vtable[12])(gpu_metrics, ctypes.byref(device_metrics, type(device_metrics).vram_used_mb.offset))
			ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p)(gpu_metrics_vtable[1])(gpu_metrics)

	return device_metrics


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
