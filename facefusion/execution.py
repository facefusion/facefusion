import shutil
import subprocess
import xml.etree.ElementTree as ElementTree
from functools import lru_cache
from typing import Any, List, Optional

from onnxruntime import get_available_providers, set_default_logger_severity

from facefusion.choices import execution_provider_set
from facefusion.typing import ExecutionDevice, ExecutionProviderKey, ExecutionProviderSet, ValueAndUnit

set_default_logger_severity(3)


def has_execution_provider(execution_provider_key : ExecutionProviderKey) -> bool:
	return execution_provider_key in get_execution_provider_set().keys()


def get_execution_provider_set() -> ExecutionProviderSet:
	available_execution_providers = get_available_providers()
	available_execution_provider_set : ExecutionProviderSet = {}

	for execution_provider_key, execution_provider_value in execution_provider_set.items():
		if execution_provider_value in available_execution_providers:
			available_execution_provider_set[execution_provider_key] = execution_provider_value
	return available_execution_provider_set


def create_execution_providers(execution_device_id : str, execution_provider_keys : List[ExecutionProviderKey]) -> List[Any]:
	execution_providers : List[Any] = []

	for execution_provider_key in execution_provider_keys:
		if execution_provider_key == 'cuda':
			execution_providers.append((execution_provider_set.get(execution_provider_key),
			{
				'device_id': execution_device_id
			}))
		if execution_provider_key == 'tensorrt':
			execution_providers.append((execution_provider_set.get(execution_provider_key),
			{
				'device_id': execution_device_id,
				'trt_engine_cache_enable': True,
				'trt_engine_cache_path': '.caches',
				'trt_timing_cache_enable': True,
				'trt_timing_cache_path': '.caches',
				'trt_builder_optimization_level': 5
			}))
		if execution_provider_key == 'openvino':
			execution_providers.append((execution_provider_set.get(execution_provider_key),
			{
				'device_type': 'GPU' if execution_device_id == '0' else 'GPU.' + execution_device_id,
				'precision': 'FP32'
			}))
		if execution_provider_key in [ 'directml', 'rocm' ]:
			execution_providers.append((execution_provider_set.get(execution_provider_key),
			{
				'device_id': execution_device_id
			}))
		if execution_provider_key == 'coreml':
			execution_providers.append(execution_provider_set.get(execution_provider_key))

	if 'cpu' in execution_provider_keys:
		execution_providers.append(execution_provider_set.get('cpu'))

	return execution_providers


def run_nvidia_smi() -> subprocess.Popen[bytes]:
	commands = [ shutil.which('nvidia-smi'), '--query', '--xml-format' ]
	return subprocess.Popen(commands, stdout = subprocess.PIPE)


@lru_cache(maxsize = None)
def detect_static_execution_devices() -> List[ExecutionDevice]:
	return detect_execution_devices()


def detect_execution_devices() -> List[ExecutionDevice]:
	execution_devices : List[ExecutionDevice] = []

	try:
		output, _ = run_nvidia_smi().communicate()
		root_element = ElementTree.fromstring(output)
	except Exception:
		root_element = ElementTree.Element('xml')

	for gpu_element in root_element.findall('gpu'):
		execution_devices.append(
		{
			'driver_version': root_element.findtext('driver_version'),
			'framework':
			{
				'name': 'CUDA',
				'version': root_element.findtext('cuda_version')
			},
			'product':
			{
				'vendor': 'NVIDIA',
				'name': gpu_element.findtext('product_name').replace('NVIDIA', '').strip()
			},
			'video_memory':
			{
				'total': create_value_and_unit(gpu_element.findtext('fb_memory_usage/total')),
				'free': create_value_and_unit(gpu_element.findtext('fb_memory_usage/free'))
			},
			'temperature':
			{
				'gpu': create_value_and_unit(gpu_element.findtext('temperature/gpu_temp')),
				'memory': create_value_and_unit(gpu_element.findtext('temperature/memory_temp'))
			},
			'utilization':
			{
				'gpu': create_value_and_unit(gpu_element.findtext('utilization/gpu_util')),
				'memory': create_value_and_unit(gpu_element.findtext('utilization/memory_util'))
			}
		})

	return execution_devices


def create_value_and_unit(text : str) -> Optional[ValueAndUnit]:
	if ' ' in text:
		value, unit = text.split(' ')

		return\
		{
			'value': int(value),
			'unit': str(unit)
		}
	return None
