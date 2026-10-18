import ctypes
from typing import List

from facefusion.libraries import amd_adlx as amd_adlx_module


def init() -> ctypes.c_void_p:
	amd_adlx_library = amd_adlx_module.create_static_library()
	session_handle = ctypes.c_void_p()

	if amd_adlx_library:
		full_version = ctypes.c_uint64()
		amd_adlx_library.ADLXQueryFullVersion(ctypes.byref(full_version))
		amd_adlx_library.ADLXInitialize(full_version.value, ctypes.byref(session_handle))

	return session_handle


def get_framework_version() -> ctypes.c_char_p:
	amd_adlx_library = amd_adlx_module.create_static_library()
	framework_version = ctypes.c_char_p()

	if amd_adlx_library:
		amd_adlx_library.ADLXQueryVersion(ctypes.byref(framework_version))

	return framework_version


def find_device_handles(session_handle : ctypes.c_void_p) -> List[ctypes.c_void_p]:
	device_handles : List[ctypes.c_void_p] = []
	device_list_handle = ctypes.c_void_p()
	get_gpus = amd_adlx_module.lookup_method(session_handle, 1, ctypes.c_int, [ ctypes.c_void_p, ctypes.c_void_p ])

	if get_gpus(session_handle, ctypes.byref(device_list_handle)) == 0:
		get_size = amd_adlx_module.lookup_method(device_list_handle, 3, ctypes.c_uint32, [ ctypes.c_void_p ])
		get_device = amd_adlx_module.lookup_method(device_list_handle, 11, ctypes.c_int, [ ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p ])

		for device_index in range(get_size(device_list_handle)):
			device_handle = ctypes.c_void_p()

			if get_device(device_list_handle, device_index, ctypes.byref(device_handle)) == 0:
				device_handles.append(device_handle)

		release(device_list_handle)

	return device_handles


def get_driver_version(device_handle : ctypes.c_void_p) -> ctypes.c_char_p:
	driver_version = ctypes.c_char_p()
	device_interface_handle = ctypes.c_void_p()
	query_interface = amd_adlx_module.lookup_method(device_handle, 2, ctypes.c_int, [ ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_void_p ])

	if query_interface(device_handle, 'IADLXGPU2', ctypes.byref(device_interface_handle)) == 0:
		get_driver_version = amd_adlx_module.lookup_method(device_interface_handle, 39, ctypes.c_int, [ ctypes.c_void_p, ctypes.c_void_p ])
		get_driver_version(device_interface_handle, ctypes.byref(driver_version))
		release(device_interface_handle)

	return driver_version


def get_device_name(device_handle : ctypes.c_void_p) -> ctypes.c_char_p:
	device_name = ctypes.c_char_p()
	get_name = amd_adlx_module.lookup_method(device_handle, 7, ctypes.c_int, [ ctypes.c_void_p, ctypes.c_void_p ])
	get_name(device_handle, ctypes.byref(device_name))

	return device_name


def get_device_memory(session_handle : ctypes.c_void_p, device_handle : ctypes.c_void_p) -> ctypes.Structure:
	device_memory = amd_adlx_module.define_device_memory()
	get_total_memory = amd_adlx_module.lookup_method(device_handle, 11, ctypes.c_int, [ ctypes.c_void_p, ctypes.c_void_p ])
	get_total_memory(device_handle, ctypes.byref(device_memory, type(device_memory).memory_total.offset))
	performance_monitoring_handle = ctypes.c_void_p()
	get_performance_monitoring_services = amd_adlx_module.lookup_method(session_handle, 9, ctypes.c_int, [ ctypes.c_void_p, ctypes.c_void_p ])

	if get_performance_monitoring_services(session_handle, ctypes.byref(performance_monitoring_handle)) == 0:
		device_info_handle = ctypes.c_void_p()
		get_current_gpu_metrics = amd_adlx_module.lookup_method(performance_monitoring_handle, 18, ctypes.c_int, [ ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p ])

		if get_current_gpu_metrics(performance_monitoring_handle, device_handle, ctypes.byref(device_info_handle)) == 0:
			get_memory_used = amd_adlx_module.lookup_method(device_info_handle, 12, ctypes.c_int, [ ctypes.c_void_p, ctypes.c_void_p ])
			get_memory_used(device_info_handle, ctypes.byref(device_memory, type(device_memory).memory_used.offset))
			release(device_info_handle)

		release(performance_monitoring_handle)

	return device_memory


def get_device_temperature(session_handle : ctypes.c_void_p, device_handle : ctypes.c_void_p) -> ctypes.c_double:
	device_temperature = ctypes.c_double()
	performance_monitoring_handle = ctypes.c_void_p()
	get_performance_monitoring_services = amd_adlx_module.lookup_method(session_handle, 9, ctypes.c_int, [ ctypes.c_void_p, ctypes.c_void_p ])

	if get_performance_monitoring_services(session_handle, ctypes.byref(performance_monitoring_handle)) == 0:
		device_info_handle = ctypes.c_void_p()
		get_current_gpu_metrics = amd_adlx_module.lookup_method(performance_monitoring_handle, 18, ctypes.c_int, [ ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p ])

		if get_current_gpu_metrics(performance_monitoring_handle, device_handle, ctypes.byref(device_info_handle)) == 0:
			get_temperature = amd_adlx_module.lookup_method(device_info_handle, 7, ctypes.c_int, [ ctypes.c_void_p, ctypes.c_void_p ])
			get_temperature(device_info_handle, ctypes.byref(device_temperature))
			release(device_info_handle)

		release(performance_monitoring_handle)

	return device_temperature


def get_device_utilization(session_handle : ctypes.c_void_p, device_handle : ctypes.c_void_p) -> ctypes.c_double:
	device_utilization = ctypes.c_double()
	performance_monitoring_handle = ctypes.c_void_p()
	get_performance_monitoring_services = amd_adlx_module.lookup_method(session_handle, 9, ctypes.c_int, [ ctypes.c_void_p, ctypes.c_void_p ])

	if get_performance_monitoring_services(session_handle, ctypes.byref(performance_monitoring_handle)) == 0:
		device_info_handle = ctypes.c_void_p()
		get_current_gpu_metrics = amd_adlx_module.lookup_method(performance_monitoring_handle, 18, ctypes.c_int, [ ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p ])

		if get_current_gpu_metrics(performance_monitoring_handle, device_handle, ctypes.byref(device_info_handle)) == 0:
			get_utilization = amd_adlx_module.lookup_method(device_info_handle, 4, ctypes.c_int, [ ctypes.c_void_p, ctypes.c_void_p ])
			get_utilization(device_info_handle, ctypes.byref(device_utilization))
			release(device_info_handle)

		release(performance_monitoring_handle)

	return device_utilization


def release(interface_handle : ctypes.c_void_p) -> None:
	release_interface = amd_adlx_module.lookup_method(interface_handle, 1, ctypes.c_long, [ ctypes.c_void_p ])
	release_interface(interface_handle)


def destroy() -> None:
	amd_adlx_library = amd_adlx_module.create_static_library()

	if amd_adlx_library:
		amd_adlx_library.ADLXTerminate()
