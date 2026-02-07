from facefusion.execution import detect_execution_devices
from facefusion.types import Metrics


def get_metrics_set() -> Metrics:
	return\
	{
		'execution_devices': detect_execution_devices()
	}
