import ctypes
from typing import List

from facefusion.libraries import nvidia_ml as nvidia_ml_module


def init() -> bool:
	nvidia_ml_library = nvidia_ml_module.create_static_library()

	if nvidia_ml_library:
		return nvidia_ml_library.nvmlInit_v2() == 0

	return False


def get_framework_version() -> ctypes.c_int:
	nvidia_ml_library = nvidia_ml_module.create_static_library()
	framework_version = ctypes.c_int()

	if nvidia_ml_library:
		nvidia_ml_library.nvmlSystemGetCudaDriverVersion(ctypes.byref(framework_version))

	return framework_version


def get_driver_version() -> ctypes.Array[ctypes.c_char]:
	nvidia_ml_library = nvidia_ml_module.create_static_library()
	driver_version = ctypes.create_string_buffer(128)

	if nvidia_ml_library:
		nvidia_ml_library.nvmlSystemGetDriverVersion(driver_version, 128)

	return driver_version


def find_device_handles() -> List[ctypes.c_void_p]:
	nvidia_ml_library = nvidia_ml_module.create_static_library()
	device_handles : List[ctypes.c_void_p] = []

	if nvidia_ml_library:
		device_count = ctypes.c_uint()
		nvidia_ml_library.nvmlDeviceGetCount_v2(ctypes.byref(device_count))

		for device_id in range(device_count.value):
			device_handle = ctypes.c_void_p()
			nvidia_ml_library.nvmlDeviceGetHandleByIndex_v2(device_id, ctypes.byref(device_handle))
			device_handles.append(device_handle)

	return device_handles


def get_device_name(device_handle : ctypes.c_void_p) -> ctypes.Array[ctypes.c_char]:
	nvidia_ml_library = nvidia_ml_module.create_static_library()
	device_name = ctypes.create_string_buffer(128)

	if nvidia_ml_library:
		nvidia_ml_library.nvmlDeviceGetName(device_handle, device_name, 128)

	return device_name


def get_device_memory(device_handle : ctypes.c_void_p) -> ctypes.Structure:
	nvidia_ml_library = nvidia_ml_module.create_static_library()
	device_memory = nvidia_ml_module.define_device_memory()

	if nvidia_ml_library:
		nvidia_ml_library.nvmlDeviceGetMemoryInfo(device_handle, ctypes.byref(device_memory))

	return device_memory


def get_device_temperature(device_handle : ctypes.c_void_p) -> ctypes.c_uint:
	nvidia_ml_library = nvidia_ml_module.create_static_library()
	device_temperature = ctypes.c_uint()

	if nvidia_ml_library:
		nvidia_ml_library.nvmlDeviceGetTemperature(device_handle, 0, ctypes.byref(device_temperature))

	return device_temperature


def get_device_utilization(device_handle : ctypes.c_void_p) -> ctypes.Structure:
	nvidia_ml_library = nvidia_ml_module.create_static_library()
	device_utilization = nvidia_ml_module.define_device_utilization()

	if nvidia_ml_library:
		nvidia_ml_library.nvmlDeviceGetUtilizationRates(device_handle, ctypes.byref(device_utilization))

	return device_utilization


def destroy() -> None:
	nvidia_ml_library = nvidia_ml_module.create_static_library()

	if nvidia_ml_library:
		nvidia_ml_library.nvmlShutdown()
