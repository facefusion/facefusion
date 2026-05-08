import ctypes
import importlib
import shutil
from pathlib import Path
from typing import List

import psutil

from facefusion import state_manager
from facefusion.libraries.nvidia_ml import create_memory_configuration, create_static_library, create_utilization_configuration
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
	nvidia_ml = create_static_library()
	graphic_devices : List[GraphicDevice] = []

	if nvidia_ml:
		nvidia_ml.nvmlInit_v2()

		device_count = ctypes.c_uint()
		nvidia_ml.nvmlDeviceGetCount_v2(ctypes.byref(device_count))

		driver_version = ctypes.create_string_buffer(80)
		nvidia_ml.nvmlSystemGetDriverVersion(driver_version, 80)

		cuda_version = ctypes.c_int()
		nvidia_ml.nvmlSystemGetCudaDriverVersion(ctypes.byref(cuda_version))

		for device_id in range(device_count.value):
			device_handle = ctypes.c_void_p()
			nvidia_ml.nvmlDeviceGetHandleByIndex_v2(device_id, ctypes.byref(device_handle))

			name = ctypes.create_string_buffer(96)
			nvidia_ml.nvmlDeviceGetName(device_handle, name, 96)

			memory = create_memory_configuration()
			nvidia_ml.nvmlDeviceGetMemoryInfo(device_handle, ctypes.byref(memory))

			temperature = ctypes.c_uint()
			nvidia_ml.nvmlDeviceGetTemperature(device_handle, 0, ctypes.byref(temperature))

			utilization = create_utilization_configuration()
			nvidia_ml.nvmlDeviceGetUtilizationRates(device_handle, ctypes.byref(utilization))

			graphic_devices.append(
			{
				'driver_version': driver_version.value.decode(),
				'framework':
				{
					'name': 'CUDA',
					'version': cuda_version.value
				},
				'product':
				{
					'vendor': 'NVIDIA',
					'name': name.value.decode()
				},
				'video_memory':
				{
					'total':
					{
						'value': memory.total // (1024 * 1024 * 1024),
						'unit': 'GB'
					},
					'used':
					{
						'value': memory.used // (1024 * 1024 * 1024),
						'unit': 'GB'
					}
				},
				'temperature':
				{
					'gpu':
					{
						'value': temperature.value,
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
						'value': utilization.gpu,
						'unit': '%'
					},
					'memory':
					{
						'value': utilization.memory,
						'unit': '%'
					}
				}
			})

		nvidia_ml.nvmlShutdown()

	return graphic_devices


def detect_amd_graphic_devices() -> List[GraphicDevice]:
	amdsmi = importlib.import_module('amdsmi')
	graphic_devices : List[GraphicDevice] = []

	amdsmi.amdsmi_init()
	handles = amdsmi.amdsmi_get_processor_handles()

	for handle in handles:
		driver_info = amdsmi.amdsmi_get_gpu_driver_info(handle)
		vram_usage = amdsmi.amdsmi_get_gpu_vram_usage(handle)
		activity = amdsmi.amdsmi_get_gpu_activity(handle)

		graphic_devices.append(
		{
			'driver_version': driver_info.get('driver_version', ''),
			'framework':
			{
				'name': 'ROCm',
				'version': driver_info.get('driver_version', '')
			},
			'product':
			{
				'vendor': 'AMD',
				'name': amdsmi.amdsmi_get_gpu_asic_info(handle).get('market_name', '')
			},
			'video_memory':
			{
				'total':
				{
					'value': vram_usage.get('vram_total', 0) // (1024 * 1024 * 1024),
					'unit': 'GB'
				},
				'used':
				{
					'value': vram_usage.get('vram_used', 0) // (1024 * 1024 * 1024),
					'unit': 'GB'
				}
			},
			'temperature':
			{
				'gpu':
				{
					'value': amdsmi.amdsmi_get_temp_metric(handle, amdsmi.AmdSmiTemperatureType.EDGE, amdsmi.AmdSmiTemperatureMetric.CURRENT) // 1000,
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
					'value': activity.get('gfx_activity', 0),
					'unit': '%'
				},
				'memory':
				{
					'value': activity.get('umc_activity', 0),
					'unit': '%'
				}
			}
		})

	amdsmi.amdsmi_shut_down()

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
