import ctypes
from functools import lru_cache
from typing import List, Optional

from facefusion.common_helper import is_linux


def resolve_library_file() -> Optional[str]:
	if is_linux():
		return 'libamd_smi.so'
	return None


@lru_cache
def create_static_library() -> Optional[ctypes.CDLL]:
	library_file = resolve_library_file()

	if library_file:
		amd_smi_library = ctypes.CDLL(library_file)
		return init_ctypes(amd_smi_library)

	return None


def define_driver_info() -> ctypes.Structure:
	return type('AMDSMI_DRIVER_INFO', (ctypes.Structure,),
	{
		'_pack_': 1,
		'_fields_':
		[
			('driver_version', ctypes.c_char * 256),
			('driver_date', ctypes.c_char * 256),
			('driver_name', ctypes.c_char * 256)
		]
	})()


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


def init_ctypes(amd_smi : ctypes.CDLL) -> ctypes.CDLL:
	amd_smi.amdsmi_init.argtypes = [ ctypes.c_uint64 ]
	amd_smi.amdsmi_init.restype = ctypes.c_uint32

	amd_smi.amdsmi_shut_down.argtypes = []
	amd_smi.amdsmi_shut_down.restype = ctypes.c_uint32

	amd_smi.amdsmi_get_socket_handles.argtypes = [ ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_void_p) ]
	amd_smi.amdsmi_get_socket_handles.restype = ctypes.c_uint32

	amd_smi.amdsmi_get_processor_handles.argtypes = [ ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_void_p) ]
	amd_smi.amdsmi_get_processor_handles.restype = ctypes.c_uint32

	amd_smi.amdsmi_get_gpu_driver_info.argtypes = [ ctypes.c_void_p, ctypes.c_void_p ]
	amd_smi.amdsmi_get_gpu_driver_info.restype = ctypes.c_uint32

	amd_smi.amdsmi_get_gpu_vram_usage.argtypes = [ ctypes.c_void_p, ctypes.c_void_p ]
	amd_smi.amdsmi_get_gpu_vram_usage.restype = ctypes.c_uint32

	amd_smi.amdsmi_get_gpu_activity.argtypes = [ ctypes.c_void_p, ctypes.c_void_p ]
	amd_smi.amdsmi_get_gpu_activity.restype = ctypes.c_uint32

	amd_smi.amdsmi_get_gpu_asic_info.argtypes = [ ctypes.c_void_p, ctypes.c_void_p ]
	amd_smi.amdsmi_get_gpu_asic_info.restype = ctypes.c_uint32

	amd_smi.amdsmi_get_temp_metric.argtypes = [ ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_int64) ]
	amd_smi.amdsmi_get_temp_metric.restype = ctypes.c_uint32

	return amd_smi


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
