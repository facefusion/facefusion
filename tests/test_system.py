import tempfile
from unittest.mock import patch

import pytest

from facefusion import state_manager
from facefusion.system import detect_disk_metrics, detect_graphic_devices, detect_memory_metrics, detect_network_metrics, detect_processor_metrics, get_metrics_set


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()

	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('execution_providers', [ 'cpu' ])


def test_get_metrics_set() -> None:
	with patch('facefusion.system.psutil.cpu_freq', create = True):
		assert get_metrics_set().get('graphic_devices') == []


def test_detect_graphic_devices() -> None:
	assert detect_graphic_devices([ 'cpu' ]) == []

	with patch('facefusion.system.detect_nvidia_ml', return_value = [ 'nvidia_ml' ]):
		with patch('facefusion.system.detect_amd_smi', return_value = [ 'amd_smi' ]):
			with patch('facefusion.system.detect_amd_adlx', return_value = [ 'amd_adlx' ]):
				assert detect_graphic_devices([ 'cuda' ]) == [ 'nvidia_ml' ]
				assert detect_graphic_devices([ 'tensorrt' ]) == [ 'nvidia_ml' ]

				with patch('facefusion.system.is_linux', return_value = True):
					assert detect_graphic_devices([ 'migraphx' ]) == [ 'amd_smi' ]

				with patch('facefusion.system.is_windows', return_value = True):
					assert detect_graphic_devices([ 'directml' ]) == [ 'amd_adlx' ]

			with patch('facefusion.system.detect_amd_adlx', return_value = []):
				with patch('facefusion.system.is_windows', return_value = True):
					assert detect_graphic_devices([ 'directml' ]) == [ 'nvidia_ml' ]


def test_detect_disk_metrics() -> None:
	with patch('facefusion.system.shutil.disk_usage') as disk_usage:
		disk_usage.return_value.total = 20 * 1024 ** 4
		disk_usage.return_value.free = 10 * 1024 ** 4
		disk_usage.return_value.used = 10 * 1024 ** 4
		disk_metrics = detect_disk_metrics([ tempfile.gettempdir() ])

	assert disk_metrics[0].get('total').get('value') == 20480
	assert disk_metrics[0].get('free').get('value') == 10240
	assert disk_metrics[0].get('utilization').get('value') == 50


def test_detect_memory_metrics() -> None:
	with patch('facefusion.system.psutil.virtual_memory') as virtual_memory:
		virtual_memory.return_value.total = 32 * 1024 ** 3
		virtual_memory.return_value.available = 16 * 1024 ** 3
		virtual_memory.return_value.percent = 50
		memory_metrics = detect_memory_metrics()

	assert memory_metrics.get('total').get('value') == 32
	assert memory_metrics.get('free').get('value') == 16
	assert memory_metrics.get('utilization').get('value') == 50


def test_detect_network_metrics() -> None:
	with patch('facefusion.system.psutil.net_io_counters') as net_io_counters:
		net_io_counters.return_value.bytes_sent = 400 * 1024 * 1024
		net_io_counters.return_value.bytes_recv = 800 * 1024 * 1024
		network_metrics = detect_network_metrics()

	assert network_metrics.get('up').get('value') == 400
	assert network_metrics.get('down').get('value') == 800


def test_detect_processor_metrics() -> None:
	with patch('facefusion.system.psutil.cpu_count', return_value = 16):
		with patch('facefusion.system.psutil.cpu_freq', create = True) as cpu_freq:
			cpu_freq.return_value.current = 3000
			with patch('facefusion.system.psutil.cpu_percent', return_value = 50):
				processor_metrics = detect_processor_metrics()

	assert processor_metrics.get('cores').get('value') == 16
	assert processor_metrics.get('frequency').get('value') == 3000
	assert processor_metrics.get('utilization').get('value') == 50
