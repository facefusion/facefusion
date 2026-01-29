import os
import platform
import subprocess
from typing import List, Optional

import psutil

from facefusion.execution import detect_execution_devices
from facefusion.types import DiskMetrics, Frequency, MemoryMetrics, Metrics, ProcessorMetrics, Utilization


def get_metrics_set() -> Metrics:
	return\
	{
		'execution_devices': detect_execution_devices(),
		'processors': get_processor_metrics(),
		'memory': get_memory_metrics(),
		'disk': get_disk_metrics()
	}


def get_processor_metrics() -> List[ProcessorMetrics]:
	processors : List[ProcessorMetrics] = []
	cpu_frequency = psutil.cpu_freq() if hasattr(psutil, 'cpu_freq') else None # TODO
	cpu_percent = psutil.cpu_percent()
	cpu_name = get_cpu_name()
	cpu_vendor = get_cpu_vendor()
	frequency : Optional[Frequency] = None
	utilization : Optional[Utilization] = None

	if cpu_frequency:
		frequency =\
		{
			'value': int(cpu_frequency.current),
			'unit': 'MHz'
		}

	if cpu_percent:
		utilization =\
		{
			'value': int(cpu_percent),
			'unit': '%'
		}

	processors.append(
	{
		'id': 0,
		'name': cpu_name,
		'vendor': cpu_vendor,
		'frequency': frequency,
		'utilization': utilization
	})

	return processors


def get_cpu_name() -> Optional[str]:
	if platform.system() == 'Windows':
		return platform.processor()

	if platform.system() == 'Linux':
		with open('/proc/cpuinfo') as cpuinfo:
			for line in cpuinfo:
				if 'model name' in line:
					return line.split(':')[1].strip()

	if platform.system() == 'Darwin':
		output = subprocess.check_output([ 'sysctl', '-n', 'machdep.cpu.brand_string' ])
		return output.decode().strip()

	return None


def get_cpu_vendor() -> Optional[str]:
	if platform.system() == 'Linux':
		with open('/proc/cpuinfo') as cpuinfo:
			for line in cpuinfo:
				if 'vendor_id' in line:
					return line.split(':')[1].strip()

	if platform.system() == 'Darwin':
		output = subprocess.check_output([ 'sysctl', '-n', 'machdep.cpu.vendor' ])
		return output.decode().strip()

	return None


def get_memory_metrics() -> MemoryMetrics:
	virtual_memory = psutil.virtual_memory()
	total_gib = virtual_memory.total // (1024 * 1024 * 1024)
	free_gib = virtual_memory.available // (1024 * 1024 * 1024)

	return\
	{
		'total':
		{
			'value': total_gib,
			'unit': 'GiB'
		},
		'free':
		{
			'value': free_gib,
			'unit': 'GiB'
		},
		'utilization':
		{
			'value': int(virtual_memory.percent),
			'unit': '%'
		}
	}


def get_disk_metrics() -> Optional[DiskMetrics]:
	temp_path = os.getcwd()
	target_mountpoint = None
	target_mountpoint_len = 0

	for partition in psutil.disk_partitions():
		if temp_path.startswith(partition.mountpoint):
			if len(partition.mountpoint) > target_mountpoint_len:
				target_mountpoint = partition.mountpoint
				target_mountpoint_len = len(partition.mountpoint)

	if target_mountpoint:
		usage = psutil.disk_usage(target_mountpoint)
		total_gib = usage.total // (1024 * 1024 * 1024)
		free_gib = usage.free // (1024 * 1024 * 1024)

		return\
		{
			'total':
			{
				'value': total_gib,
				'unit': 'GiB'
			},
			'free':
			{
				'value': free_gib,
				'unit': 'GiB'
			},
			'utilization':
			{
				'value': int(usage.percent),
				'unit': '%'
			}
		}

	return None
