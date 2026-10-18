import shutil
from pathlib import Path
from typing import List

import psutil

from facefusion import state_manager
from facefusion.common_helper import is_linux, is_windows
from facefusion.devices import amd_adlx, amd_smi, nvidia_ml
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
		graphic_devices = detect_nvidia_ml()

		if graphic_devices:
			return graphic_devices

	if is_linux() and 'migraphx' in execution_providers:
		graphic_devices = detect_amd_smi()

		if graphic_devices:
			return graphic_devices

	if is_windows() and 'directml' in execution_providers:
		graphic_devices = detect_amd_adlx()

		if graphic_devices:
			return graphic_devices

		graphic_devices = detect_nvidia_ml()

		if graphic_devices:
			return graphic_devices

	return []


def detect_nvidia_ml() -> List[GraphicDevice]:
	graphic_devices : List[GraphicDevice] = []

	if nvidia_ml.init():
		framework_version = nvidia_ml.get_framework_version()
		driver_version = nvidia_ml.get_driver_version()

		for device_handle in nvidia_ml.find_device_handles():
			device_name = nvidia_ml.get_device_name(device_handle)
			device_memory = nvidia_ml.get_device_memory(device_handle)
			device_temperature = nvidia_ml.get_device_temperature(device_handle)
			device_utilization = nvidia_ml.get_device_utilization(device_handle)

			graphic_devices.append(
			{
				'driver_version': driver_version.value.decode(),
				'framework':
				{
					'name': 'CUDA',
					'version': str(framework_version.value)
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

		nvidia_ml.destroy()

	return graphic_devices


def detect_amd_smi() -> List[GraphicDevice]:
	graphic_devices : List[GraphicDevice] = []

	if amd_smi.init():
		framework_major_version, framework_minor_version, framework_patch_version = amd_smi.get_framework_version()

		for device_handle in amd_smi.find_device_handles():
			driver_version = amd_smi.get_driver_version(device_handle)
			device_name = amd_smi.get_device_name(device_handle)
			device_memory = amd_smi.get_device_memory(device_handle)
			device_temperature = amd_smi.get_device_temperature(device_handle)
			device_utilization = amd_smi.get_device_utilization(device_handle)

			graphic_devices.append(
			{
				'driver_version': driver_version.value.decode(),
				'framework':
				{
					'name': 'ROCm',
					'version': str(framework_major_version.value) + '.' + str(framework_minor_version.value) + '.' + str(framework_patch_version.value)
				},
				'product':
				{
					'vendor': 'AMD',
					'name': device_name.value.decode()
				},
				'memory':
				{
					'total':
					{
						'value': device_memory.memory_total // 1024,
						'unit': 'GB'
					},
					'used':
					{
						'value': device_memory.memory_used // 1024,
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

		amd_smi.destroy()

	return graphic_devices


def detect_amd_adlx() -> List[GraphicDevice]:
	graphic_devices : List[GraphicDevice] = []
	system_handle = amd_adlx.init()

	if system_handle.value:
		framework_version = amd_adlx.get_framework_version()
		performance_monitoring_handle = amd_adlx.get_performance_monitoring_handle(system_handle)

		for device_handle in amd_adlx.find_device_handles(system_handle):
			driver_version = amd_adlx.get_driver_version(device_handle)
			device_name = amd_adlx.get_device_name(device_handle)
			device_memory = amd_adlx.get_device_memory(performance_monitoring_handle, device_handle)
			device_temperature = amd_adlx.get_device_temperature(performance_monitoring_handle, device_handle)
			device_utilization = amd_adlx.get_device_utilization(performance_monitoring_handle, device_handle)

			graphic_devices.append(
			{
				'driver_version': driver_version.value.decode(),
				'framework':
				{
					'name': 'ADLX',
					'version': framework_version.value.decode()
				},
				'product':
				{
					'vendor': 'AMD',
					'name': device_name.value.decode()
				},
				'memory':
				{
					'total':
					{
						'value': device_memory.memory_total // 1024,
						'unit': 'GB'
					},
					'used':
					{
						'value': device_memory.memory_used // 1024,
						'unit': 'GB'
					}
				},
				'temperature':
				{
					'gpu':
					{
						'value': int(device_temperature.value),
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
						'value': int(device_utilization.value),
						'unit': '%'
					},
					'memory':
					{
						'value': 0,
						'unit': '%'
					}
				}
			})

			amd_adlx.release_interface(device_handle)

		if performance_monitoring_handle.value:
			amd_adlx.release_interface(performance_monitoring_handle)

		amd_adlx.destroy()

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
