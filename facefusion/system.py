import ctypes
import shutil
from pathlib import Path
from typing import List

import psutil

from facefusion import state_manager
from facefusion.common_helper import is_linux, is_windows
from facefusion.libraries import amd_adlx as amd_adlx_module, amd_smi as amd_smi_module, nvidia_ml as nvidia_ml_module, rocm_core as rocm_core_module
from facefusion.types import DiskMetrics, ExecutionProvider, GraphicDevice, MemoryMetrics, Metrics, NetworkMetrics, ProcessorMetrics


def get_metrics_set() -> Metrics:
	drive_path = Path(state_manager.get_temp_path()).anchor

	return\
	{
		'graphic_devices': detect_graphic_devices(state_manager.get_item('execution_providers')),
		'disks': detect_disk_metrics([ drive_path ]),
		'memory': detect_memory_metrics(),
		'network': detect_network_metrics(),
		'processor': detect_processor_metrics()
	}


def detect_graphic_devices(execution_providers : List[ExecutionProvider]) -> List[GraphicDevice]:
	if 'cuda' in execution_providers or 'tensorrt' in execution_providers:
		return detect_nvidia_ml()
	if is_linux() and 'migraphx' in execution_providers:
		return detect_amd_smi()
	if is_windows() and 'directml' in execution_providers:
		return detect_amd_adlx()
	return []


def detect_nvidia_ml() -> List[GraphicDevice]:
	nvidia_ml_library = nvidia_ml_module.create_static_library()
	graphic_devices : List[GraphicDevice] = []

	if nvidia_ml_library:
		nvidia_ml_library.nvmlInit_v2()

		driver_version = ctypes.create_string_buffer(128)
		nvidia_ml_library.nvmlSystemGetDriverVersion(driver_version, 128)

		cuda_version = ctypes.c_int()
		nvidia_ml_library.nvmlSystemGetCudaDriverVersion(ctypes.byref(cuda_version))

		for device_handle in nvidia_ml_module.find_device_handles(nvidia_ml_library):
			device_name = ctypes.create_string_buffer(128)
			nvidia_ml_library.nvmlDeviceGetName(device_handle, device_name, 128)

			device_memory = nvidia_ml_module.define_device_memory()
			nvidia_ml_library.nvmlDeviceGetMemoryInfo(device_handle, ctypes.byref(device_memory))

			device_temperature = ctypes.c_uint()
			nvidia_ml_library.nvmlDeviceGetTemperature(device_handle, 0, ctypes.byref(device_temperature))

			device_utilization = nvidia_ml_module.define_device_utilization()
			nvidia_ml_library.nvmlDeviceGetUtilizationRates(device_handle, ctypes.byref(device_utilization))

			graphic_devices.append(
			{
				'driver_version': driver_version.value.decode(),
				'framework':
				{
					'name': 'CUDA',
					'version': str(cuda_version.value)
				},
				'product':
				{
					'vendor': 'NVIDIA',
					'name': device_name.value.decode()
				},
				'memory':
				{
					'total':
					{
						'value': device_memory.total // (1024 * 1024 * 1024),
						'unit': 'GB'
					},
					'used':
					{
						'value': device_memory.used // (1024 * 1024 * 1024),
						'unit': 'GB'
					}
				},
				'temperature':
				{
					'gpu':
					{
						'value': device_temperature.value,
						'unit': 'C'
					},
					'memory':
					{
						'value': 0,
						'unit': '%'
					}
				},
				'utilization':
				{
					'gpu':
					{
						'value': device_utilization.gpu,
						'unit': '%'
					},
					'memory':
					{
						'value': device_utilization.memory,
						'unit': '%'
					}
				}
			})

		nvidia_ml_library.nvmlShutdown()

	return graphic_devices


def detect_amd_smi() -> List[GraphicDevice]:
	amd_smi_library = amd_smi_module.create_static_library()
	graphic_devices : List[GraphicDevice] = []

	if amd_smi_library:
		amd_smi_library.amdsmi_init(ctypes.c_uint64(2))

		rocm_core_library = rocm_core_module.create_static_library()
		rocm_major_version = ctypes.c_uint()
		rocm_minor_version = ctypes.c_uint()
		rocm_patch_version = ctypes.c_uint()

		if rocm_core_library:
			rocm_core_library.getROCmVersion(ctypes.byref(rocm_major_version), ctypes.byref(rocm_minor_version), ctypes.byref(rocm_patch_version))

		for device_handle in amd_smi_module.find_device_handles(amd_smi_library):
			product_info = amd_smi_module.define_product_info()
			amd_smi_library.amdsmi_get_gpu_asic_info(device_handle, ctypes.byref(product_info))

			device_memory = amd_smi_module.define_device_memory()
			amd_smi_library.amdsmi_get_gpu_vram_usage(device_handle, ctypes.byref(device_memory))

			device_temperature = ctypes.c_int64()
			amd_smi_library.amdsmi_get_temp_metric(device_handle, 0, 0, ctypes.byref(device_temperature))

			device_utilization = amd_smi_module.define_device_utilization()
			amd_smi_library.amdsmi_get_gpu_activity(device_handle, ctypes.byref(device_utilization))

			graphic_devices.append(
			{
				'driver_version': '0.0.0',
				'framework':
				{
					'name': 'ROCm',
					'version': str(rocm_major_version.value) + '.' + str(rocm_minor_version.value) + '.' + str(rocm_patch_version.value)
				},
				'product':
				{
					'vendor': 'AMD',
					'name': product_info.market_name.decode()
				},
				'memory':
				{
					'total':
					{
						'value': device_memory.vram_total // 1024,
						'unit': 'GB'
					},
					'used':
					{
						'value': device_memory.vram_used // 1024,
						'unit': 'GB'
					}
				},
				'temperature':
				{
					'gpu':
					{
						'value': device_temperature.value // 1000,
						'unit': 'C'
					},
					'memory':
					{
						'value': 0,
						'unit': '%'
					}
				},
				'utilization':
				{
					'gpu':
					{
						'value': device_utilization.gfx_activity,
						'unit': '%'
					},
					'memory':
					{
						'value': device_utilization.umc_activity,
						'unit': '%'
					}
				}
			})

		amd_smi_library.amdsmi_shut_down()

	return graphic_devices


def detect_amd_adlx() -> List[GraphicDevice]:
	amd_adlx_library = amd_adlx_module.create_static_library()
	graphic_devices : List[GraphicDevice] = []

	if amd_adlx_library:
		full_version = ctypes.c_uint64()
		amd_adlx_library.ADLXQueryFullVersion(ctypes.byref(full_version))
		adlx_version = ctypes.c_char_p()
		amd_adlx_library.ADLXQueryVersion(ctypes.byref(adlx_version))
		amd_adlx_library.system = ctypes.c_void_p()

		if not amd_adlx_library.ADLXInitialize(full_version.value, ctypes.byref(amd_adlx_library.system)):
			amd_adlx_library.performance_monitoring = ctypes.c_void_p()
			system_vtable = ctypes.cast(amd_adlx_library.system, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
			ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)(system_vtable[9])(amd_adlx_library.system, ctypes.byref(amd_adlx_library.performance_monitoring))

			device_handles = amd_adlx_module.find_device_handles(amd_adlx_library)

			for device_handle in device_handles:
				#gpu_vtable = ctypes.cast(device_handle, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
				product_info = amd_adlx_module.get_product_info(device_handle)
				device_metrics = amd_adlx_module.get_device_metrics(amd_adlx_library, device_handle)

				graphic_devices.append(
				{
					'driver_version': '0.0.0',
					'framework':
					{
						'name': 'ADLX',
						'version': adlx_version.value.decode()
					},
					'product':
					{
						'vendor': 'AMD',
						'name': product_info.name.decode()
					},
					'memory':
					{
						'total':
						{
							'value': product_info.vram_total_mb // 1024,
							'unit': 'GB'
						},
						'used':
						{
							'value': device_metrics.vram_used_mb // 1024,
							'unit': 'GB'
						}
					},
					'temperature':
					{
						'gpu':
						{
							'value': int(device_metrics.temperature),
							'unit': 'C'
						},
						'memory':
						{
							'value': 0,
							'unit': '%'
						}
					},
					'utilization':
					{
						'gpu':
						{
							'value': int(device_metrics.utilization),
							'unit': '%'
						},
						'memory':
						{
							'value': 0,
							'unit': '%'
						}
					}
				})

				#ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p)(gpu_vtable[1])(device_handle)

			#if amd_adlx_library.performance_monitoring.value:
				#performance_monitoring_vtable = ctypes.cast(amd_adlx_library.performance_monitoring, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
				#ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p)(performance_monitoring_vtable[1])(amd_adlx_library.performance_monitoring)

			amd_adlx_library.ADLXTerminate()

	return graphic_devices


def detect_disk_metrics(drive_paths : List[str]) -> List[DiskMetrics]:
	disk_metrics : List[DiskMetrics] = []

	for drive_path in drive_paths:
		disk_usage = shutil.disk_usage(drive_path)

		disk_metrics.append(
		{
			'total':
			{
				'value': int(disk_usage.total / (1024 * 1024 * 1024)),
				'unit': 'GB'
			},
			'free':
			{
				'value': int(disk_usage.free / (1024 * 1024 * 1024)),
				'unit': 'GB'
			},
			'utilization':
			{
				'value': int(disk_usage.used / disk_usage.total * 100),
				'unit': '%'
			}
		})

	return disk_metrics


def detect_memory_metrics() -> MemoryMetrics:
	virtual_memory = psutil.virtual_memory()

	return\
	{
		'total':
		{
			'value': int(virtual_memory.total / (1024 * 1024 * 1024)),
			'unit': 'GB'
		},
		'free':
		{
			'value': int(virtual_memory.available / (1024 * 1024 * 1024)),
			'unit': 'GB'
		},
		'utilization':
		{
			'value': int(virtual_memory.percent),
			'unit': '%'
		}
	}


def detect_network_metrics() -> NetworkMetrics:
	network_io = psutil.net_io_counters()

	return\
	{
		'up':
		{
			'value': int(network_io.bytes_sent / (1024 * 1024)),
			'unit': 'MB'
		},
		'down':
		{
			'value': int(network_io.bytes_recv / (1024 * 1024)),
			'unit': 'MB'
		}
	}


def detect_processor_metrics() -> ProcessorMetrics:
	cpu_count = psutil.cpu_count()
	cpu_frequency = psutil.cpu_freq()

	return\
	{
		'cores':
		{
			'value': int(cpu_count),
			'unit': 'cores'
		},
		'frequency':
		{
			'value': int(cpu_frequency.current),
			'unit': 'MHz'
		},
		'utilization':
		{
			'value': int(psutil.cpu_percent()),
			'unit': '%'
		}
	}
