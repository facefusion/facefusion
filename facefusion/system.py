import shutil

from facefusion.execution import detect_execution_devices
from facefusion.types import DiskMetrics, Metrics


def get_metrics_set() -> Metrics:
	return\
	{
		'execution_devices': detect_execution_devices(),
		'disk': detect_disk_metrics()
	}


def detect_disk_metrics() -> DiskMetrics:
	usage = shutil.disk_usage('.')

	return\
	{
		'total':
		{
			'value': int(usage.total / (1024 * 1024 * 1024)),
			'unit': 'GiB'
		},
		'free':
		{
			'value': int(usage.free / (1024 * 1024 * 1024)),
			'unit': 'GiB'
		},
		'utilization':
		{
			'value': int(usage.used / usage.total * 100),
			'unit': '%'
		}
	}
