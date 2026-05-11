import ctypes
import ctypes.util
from functools import lru_cache
from typing import List, Optional


@lru_cache
def create_static_library() -> Optional[ctypes.CDLL]:
	library_path = ctypes.util.find_library('amd_smi')

	if library_path:
		library = ctypes.CDLL(library_path)

		if library:
			return init_ctypes(library)

	return None


def init_ctypes(library : ctypes.CDLL) -> ctypes.CDLL:
	library.amdsmi_init.argtypes = [ ctypes.c_uint64 ]
	library.amdsmi_init.restype = ctypes.c_uint32

	library.amdsmi_shut_down.argtypes = []
	library.amdsmi_shut_down.restype = ctypes.c_uint32

	library.amdsmi_get_socket_handles.argtypes = [ ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_void_p) ]
	library.amdsmi_get_socket_handles.restype = ctypes.c_uint32

	library.amdsmi_get_processor_handles.argtypes = [ ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_void_p) ]
	library.amdsmi_get_processor_handles.restype = ctypes.c_uint32

	library.amdsmi_get_gpu_vram_usage.argtypes = [ ctypes.c_void_p, ctypes.c_void_p ]
	library.amdsmi_get_gpu_vram_usage.restype = ctypes.c_uint32

	library.amdsmi_get_gpu_activity.argtypes = [ ctypes.c_void_p, ctypes.c_void_p ]
	library.amdsmi_get_gpu_activity.restype = ctypes.c_uint32

	library.amdsmi_get_gpu_asic_info.argtypes = [ ctypes.c_void_p, ctypes.c_void_p ]
	library.amdsmi_get_gpu_asic_info.restype = ctypes.c_uint32

	library.amdsmi_get_temp_metric.argtypes = [ ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_int64) ]
	library.amdsmi_get_temp_metric.restype = ctypes.c_uint32

	return library


def find_device_handles(amd_smi_library : ctypes.CDLL) -> List[ctypes.c_void_p]:
	device_handles : List[ctypes.c_void_p] = []

	socket_count = ctypes.c_uint32()
	amd_smi_library.amdsmi_get_socket_handles(ctypes.byref(socket_count), ctypes.POINTER(ctypes.c_void_p)())
	socket_handles = (ctypes.c_void_p * socket_count.value)()
	amd_smi_library.amdsmi_get_socket_handles(ctypes.byref(socket_count), socket_handles)

	for socket_index in range(socket_count.value):
		device_count = ctypes.c_uint32()
		amd_smi_library.amdsmi_get_processor_handles(socket_handles[socket_index], ctypes.byref(device_count), ctypes.POINTER(ctypes.c_void_p)())
		processor_handles = (ctypes.c_void_p * device_count.value)()
		amd_smi_library.amdsmi_get_processor_handles(socket_handles[socket_index], ctypes.byref(device_count), processor_handles)

		for device_index in range(device_count.value):
			device_handles.append(ctypes.c_void_p(processor_handles[device_index]))

	return device_handles


def define_product_info() -> ctypes.Structure:
	return type('AMDSMI_ASIC_INFO', (ctypes.Structure,),
	{
		'_pack_': 1,
		'_fields_':
		[
			('market_name', ctypes.c_char * 256),
			('vendor_id', ctypes.c_uint32),
			('vendor_name', ctypes.c_char * 256),
			('subvendor_id', ctypes.c_uint32),
			('device_id', ctypes.c_uint64),
			('rev_id', ctypes.c_uint32),
			('asic_serial', ctypes.c_char * 256),
			('oam_id', ctypes.c_uint32),
			('num_of_compute_units', ctypes.c_uint32),
			('padding', ctypes.c_ubyte * 4),
			('target_graphics_version', ctypes.c_uint64),
			('subsystem_id', ctypes.c_uint32),
			('reserved', ctypes.c_uint32 * 21)
		]
	})()


def define_device_memory() -> ctypes.Structure:
	return type('AMDSMI_VRAM_USAGE', (ctypes.Structure,),
	{
		'_pack_': 1,
		'_fields_':
		[
			('vram_total', ctypes.c_uint32),
			('vram_used', ctypes.c_uint32),
			('reserved', ctypes.c_uint32 * 2)
		]
	})()


def define_device_utilization() -> ctypes.Structure:
	return type('AMDSMI_ENGINE_USAGE', (ctypes.Structure,),
	{
		'_pack_': 1,
		'_fields_':
		[
			('gfx_activity', ctypes.c_uint32),
			('umc_activity', ctypes.c_uint32),
			('mm_activity', ctypes.c_uint32),
			('reserved', ctypes.c_uint32 * 13)
		]
	})()
