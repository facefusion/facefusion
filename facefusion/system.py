import importlib
import shutil
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

import psutil

from facefusion import state_manager
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


@lru_cache()
def detect_static_graphic_devices(execution_providers : Tuple[ExecutionProvider, ...]) -> List[GraphicDevice]:
	return detect_graphic_devices(execution_providers)


def detect_graphic_devices(execution_providers : Tuple[ExecutionProvider, ...]) -> List[GraphicDevice]:
	if any(execution_provider in [ 'rocm', 'migraphx' ] for execution_provider in execution_providers):
		return detect_amd_graphic_devices()
	if any(execution_provider in [ 'cuda', 'tensorrt' ] for execution_provider in execution_providers):
		return detect_nvidia_graphic_devices()
	return []


def detect_nvidia_graphic_devices() -> List[GraphicDevice]:
	pynvml = importlib.import_module('pynvml')
	graphic_devices : List[GraphicDevice] = []

	pynvml.nvmlInit()
	device_count = pynvml.nvmlDeviceGetCount()

	for device_id in range(device_count):
		handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)

		graphic_devices.append(
		{
			'driver_version': pynvml.nvmlSystemGetDriverVersion(),
			'framework':
			{
				'name': 'CUDA',
				'version': pynvml.nvmlSystemGetCudaDriverVersion()
			},
			'product':
			{
				'vendor': 'NVIDIA',
				'name': pynvml.nvmlDeviceGetName(handle)
			},
			'video_memory':
			{
				'total':
				{
					'value': pynvml.nvmlDeviceGetMemoryInfo(handle).total // (1024 * 1024 * 1024),
					'unit': 'GB'
				},
				'free':
				{
					'value': pynvml.nvmlDeviceGetMemoryInfo(handle).free // (1024 * 1024 * 1024),
					'unit': 'GB'
				}
			},
			'temperature':
			{
				'gpu':
				{
					'value': pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU),
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
					'value': pynvml.nvmlDeviceGetUtilizationRates(handle).gpu,
					'unit': '%'
				},
				'memory':
				{
					'value': pynvml.nvmlDeviceGetUtilizationRates(handle).memory,
					'unit': '%'
				}
			}
		})

	pynvml.nvmlShutdown()

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
				'free':
				{
					'value': (vram_usage.get('vram_total', 0) - vram_usage.get('vram_used', 0)) // (1024 * 1024 * 1024),
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
