import shutil
from functools import lru_cache
from pathlib import Path
from typing import List

import psutil
import pynvml

from facefusion import state_manager
from facefusion.types import DiskMetrics, ExecutionDevice, MemoryMetrics, Metrics, NetworkMetrics, ProcessorMetrics


def get_metrics_set() -> Metrics:
	drive_path = Path(state_manager.get_temp_path()).anchor

	return\
	{
		'execution_devices': detect_execution_devices(),
		'disks': detect_disk_metrics([ drive_path ]),
		'memory': detect_memory_metrics(),
		'network': detect_network_metrics(),
		'processor': detect_processor_metrics()
	}


@lru_cache()
def detect_static_execution_devices() -> List[ExecutionDevice]:
	return detect_execution_devices()


def detect_execution_devices() -> List[ExecutionDevice]:
	execution_devices : List[ExecutionDevice] = []

	try:
		pynvml.nvmlInit()
		device_count = pynvml.nvmlDeviceGetCount()

		for device_id in range(device_count):
			handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)

			execution_devices.append(
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
	except Exception:
		pass

	return execution_devices


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
