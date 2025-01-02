import shutil
import subprocess
import xml.etree.ElementTree as ElementTree
from functools import lru_cache
from typing import Any, List, Optional

from onnxruntime import get_available_providers, set_default_logger_severity

import facefusion.choices
from facefusion.typing import ExecutionDevice, ExecutionProvider, ValueAndUnit

set_default_logger_severity(3)


def has_execution_provider(execution_provider : ExecutionProvider) -> bool:
	return execution_provider in get_available_execution_providers()


def get_available_execution_providers() -> List[ExecutionProvider]:
	inference_execution_providers = get_available_providers()
	available_execution_providers = []

	for execution_provider, execution_provider_value in facefusion.choices.execution_provider_set.items():
		if execution_provider_value in inference_execution_providers:
			available_execution_providers.append(execution_provider)

	return available_execution_providers


def create_inference_execution_providers(execution_device_id : str, execution_providers : List[ExecutionProvider]) -> List[Any]:
	inference_execution_providers : List[Any] = []

	for execution_provider in execution_providers:
		if execution_provider == 'cuda':
			inference_execution_providers.append((facefusion.choices.execution_provider_set.get(execution_provider),
			{
				'device_id': execution_device_id,
				'cudnn_conv_algo_search': 'DEFAULT' if is_geforce_16_series() else 'EXHAUSTIVE'
			}))
		if execution_provider == 'tensorrt':
			inference_execution_providers.append((facefusion.choices.execution_provider_set.get(execution_provider),
			{
				'device_id': execution_device_id,
				'trt_engine_cache_enable': True,
				'trt_engine_cache_path': '.caches',
				'trt_timing_cache_enable': True,
				'trt_timing_cache_path': '.caches',
				'trt_builder_optimization_level': 5
			}))
		if execution_provider == 'openvino':
			inference_execution_providers.append((facefusion.choices.execution_provider_set.get(execution_provider),
			{
				'device_type': 'GPU' if execution_device_id == '0' else 'GPU.' + execution_device_id,
				'precision': 'FP32'
			}))
		if execution_provider in [ 'directml', 'rocm' ]:
			inference_execution_providers.append((facefusion.choices.execution_provider_set.get(execution_provider),
			{
				'device_id': execution_device_id
			}))
		if execution_provider == 'coreml':
			inference_execution_providers.append(facefusion.choices.execution_provider_set.get(execution_provider))

	if 'cpu' in execution_providers:
		inference_execution_providers.append(facefusion.choices.execution_provider_set.get('cpu'))

	return inference_execution_providers


def is_geforce_16_series() -> bool:
	execution_devices = detect_static_execution_devices()
	product_names = ('GeForce GTX 1630', 'GeForce GTX 1650', 'GeForce GTX 1660')

	return any(execution_device.get('product').get('name').startswith(product_names) for execution_device in execution_devices)


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
