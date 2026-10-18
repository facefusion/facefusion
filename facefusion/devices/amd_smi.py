import ctypes
from typing import List, Tuple

from facefusion.libraries import amd_smi as amd_smi_module, rocm_core as rocm_core_module


def init() -> bool:
	amd_smi_library = amd_smi_module.create_static_library()

	if amd_smi_library:
		return amd_smi_library.amdsmi_init(ctypes.c_uint64(2)) == 0

	return False


def get_framework_version() -> Tuple[ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]:
	rocm_core_library = rocm_core_module.create_static_library()
	framework_major_version = ctypes.c_uint()
	framework_minor_version = ctypes.c_uint()
	framework_patch_version = ctypes.c_uint()

	if rocm_core_library:
		rocm_core_library.getROCmVersion(ctypes.byref(framework_major_version), ctypes.byref(framework_minor_version), ctypes.byref(framework_patch_version))

	return framework_major_version, framework_minor_version, framework_patch_version


def find_device_handles() -> List[ctypes.c_void_p]:
	amd_smi_library = amd_smi_module.create_static_library()
	device_handles : List[ctypes.c_void_p] = []

	if amd_smi_library:
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


def get_driver_version(device_handle : ctypes.c_void_p) -> ctypes.c_char_p:
	amd_smi_library = amd_smi_module.create_static_library()
	driver_info = amd_smi_module.define_driver_info()

	if amd_smi_library:
		amd_smi_library.amdsmi_get_gpu_driver_info(device_handle, ctypes.byref(driver_info))

	return ctypes.c_char_p(driver_info.driver_version)


def get_device_name(device_handle : ctypes.c_void_p) -> ctypes.c_char_p:
	amd_smi_library = amd_smi_module.create_static_library()
	product_info = amd_smi_module.define_product_info()

	if amd_smi_library:
		amd_smi_library.amdsmi_get_gpu_asic_info(device_handle, ctypes.byref(product_info))

	return ctypes.c_char_p(product_info.market_name)


def get_device_memory(device_handle : ctypes.c_void_p) -> ctypes.Structure:
	amd_smi_library = amd_smi_module.create_static_library()
	device_memory = amd_smi_module.define_device_memory()

	if amd_smi_library:
		amd_smi_library.amdsmi_get_gpu_vram_usage(device_handle, ctypes.byref(device_memory))

	return device_memory


def get_device_temperature(device_handle : ctypes.c_void_p) -> ctypes.c_int64:
	amd_smi_library = amd_smi_module.create_static_library()
	device_temperature = ctypes.c_int64()

	if amd_smi_library:
		amd_smi_library.amdsmi_get_temp_metric(device_handle, 0, 0, ctypes.byref(device_temperature))

	return device_temperature


def get_device_utilization(device_handle : ctypes.c_void_p) -> ctypes.Structure:
	amd_smi_library = amd_smi_module.create_static_library()
	device_utilization = amd_smi_module.define_device_utilization()

	if amd_smi_library:
		amd_smi_library.amdsmi_get_gpu_activity(device_handle, ctypes.byref(device_utilization))

	return device_utilization


def destroy() -> None:
	amd_smi_library = amd_smi_module.create_static_library()

	if amd_smi_library:
		amd_smi_library.amdsmi_shut_down()
