import shutil
from typing import List

from facefusion import state_manager
from facefusion.execution import detect_execution_devices
from facefusion.types import DiskMetrics, Metrics


def get_metrics_set() -> Metrics:
	return\
	{
		'execution_devices': detect_execution_devices(),
		'disks': detect_disk_metrics([ state_manager.get_temp_path() ])
	}


def detect_disk_metrics(drive_paths : List[str]) -> List[DiskMetrics]:
	disk_metrics : List[DiskMetrics] = []

	for drive_path in drive_paths:
		disk_usage = shutil.disk_usage(drive_path)

		disk_metrics.append(
		{
			'total':
			{
				'value': int(disk_usage.total / (1024 * 1024 * 1024)),
				'unit': 'GiB'
			},
			'free':
			{
				'value': int(disk_usage.free / (1024 * 1024 * 1024)),
				'unit': 'GiB'
			},
			'utilization':
			{
				'value': int(disk_usage.used / disk_usage.total * 100),
				'unit': '%'
			}
		})

	return disk_metrics
