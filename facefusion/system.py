import ctypes
import shutil
from pathlib import Path
from typing import List

import psutil

from facefusion import state_manager
from facefusion.libraries import amd_smi as amd_smi_module, nvidia_ml as nvidia_ml_module
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
	if 'rocm' in execution_providers or 'migraphx' in execution_providers:
		return detect_amd_graphic_devices()
	if 'cuda' in execution_providers or 'tensorrt' in execution_providers:
		return detect_nvidia_graphic_devices()
	return []


def detect_nvidia_graphic_devices() -> List[GraphicDevice]:
	nvidia_ml_library = nvidia_ml_module.create_static_library()
	graphic_devices : List[GraphicDevice] = []

	if nvidia_ml_library:
		nvidia_ml_library.nvmlInit_v2()

		driver_version = ctypes.create_string_buffer(80)
		nvidia_ml_library.nvmlSystemGetDriverVersion(driver_version, 80)

		cuda_version = ctypes.c_int()
		nvidia_ml_library.nvmlSystemGetCudaDriverVersion(ctypes.byref(cuda_version))

		for device_handle in nvidia_ml_module.find_device_handles(nvidia_ml_library):
			device_name = ctypes.create_string_buffer(96)
			nvidia_ml_library.nvmlDeviceGetName(device_handle, device_name, 96)

			device_memory = nvidia_ml_module.create_memory_configuration()
			nvidia_ml_library.nvmlDeviceGetMemoryInfo(device_handle, ctypes.byref(device_memory))

			device_temperature = ctypes.c_uint()
			nvidia_ml_library.nvmlDeviceGetTemperature(device_handle, 0, ctypes.byref(device_temperature))

			device_utilization = nvidia_ml_module.create_utilization_configuration()
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


def detect_amd_graphic_devices() -> List[GraphicDevice]:
	amd_smi_library = amd_smi_module.create_static_library()
	graphic_devices : List[GraphicDevice] = []

	if amd_smi_library:
		amd_smi_library.amdsmi_init(ctypes.c_uint64(2))

		rocm_version = amd_smi_module.create_rocm_version_configuration()
		amd_smi_library.amdsmi_get_lib_version(ctypes.byref(rocm_version))

		for device_handle in amd_smi_module.find_device_handles(amd_smi_library):
			driver_info = amd_smi_module.create_driver_info_configuration()
			amd_smi_library.amdsmi_get_gpu_driver_info(device_handle, ctypes.byref(driver_info))

			product_info = amd_smi_module.create_product_info_configuration()
			amd_smi_library.amdsmi_get_gpu_asic_info(device_handle, ctypes.byref(product_info))

			device_memory = amd_smi_module.create_device_memory_configuration()
			amd_smi_library.amdsmi_get_gpu_vram_usage(device_handle, ctypes.byref(device_memory))

			device_temperature = ctypes.c_int64()
			amd_smi_library.amdsmi_get_temp_metric(device_handle, 0, 0, ctypes.byref(device_temperature))

			device_utilization = amd_smi_module.create_device_utilization_configuration()
			amd_smi_library.amdsmi_get_gpu_activity(device_handle, ctypes.byref(device_utilization))

			graphic_devices.append(
			{
				'driver_version': driver_info.driver_version.decode(),
				'framework':
				{
					'name': 'ROCm',
					'version': str(rocm_version.major) + '.' + str(rocm_version.minor) + '.' + str(rocm_version.patch)
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
						'value': device_memory.vram_total // (1024 * 1024 * 1024),
						'unit': 'GB'
					},
					'used':
					{
						'value': device_memory.vram_used // (1024 * 1024 * 1024),
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
		'sent':
		{
			'value': int(network_io.bytes_sent / (1024 * 1024)),
			'unit': 'MB'
		},
		'received':
		{
			'value': int(network_io.bytes_recv / (1024 * 1024)),
			'unit': 'MB'
		}
	}


def detect_processor_metrics() -> ProcessorMetrics:
	cpu_frequency = psutil.cpu_freq()

	return\
	{
		'cores':
		{
			'value': psutil.cpu_count(logical = True),
			'unit': 'cores'
		},
		'frequency':
		{
			'value': int(cpu_frequency.current),
			'unit': 'MHz'
		},
		'utilization':
		{
			'value': int(psutil.cpu_percent(interval = None)),
			'unit': '%'
		}
	}
