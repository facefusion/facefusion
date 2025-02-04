<<<<<<< HEAD
from typing import List, Any
from functools import lru_cache
import subprocess
import xml.etree.ElementTree as ElementTree
import onnxruntime

from facefusion.typing import ExecutionDevice, ValueAndUnit


def encode_execution_providers(execution_providers : List[str]) -> List[str]:
	return [ execution_provider.replace('ExecutionProvider', '').lower() for execution_provider in execution_providers ]


def decode_execution_providers(execution_providers : List[str]) -> List[str]:
	available_execution_providers = onnxruntime.get_available_providers()
	encoded_execution_providers = encode_execution_providers(available_execution_providers)

	return [ execution_provider for execution_provider, encoded_execution_provider in zip(available_execution_providers, encoded_execution_providers) if any(execution_provider in encoded_execution_provider for execution_provider in execution_providers) ]


def has_execution_provider(execution_provider : str) -> bool:
	return execution_provider in onnxruntime.get_available_providers()


def apply_execution_provider_options(execution_device_id : str, execution_providers : List[str]) -> List[Any]:
	execution_providers_with_options : List[Any] = []

	for execution_provider in execution_providers:
		if execution_provider == 'CUDAExecutionProvider':
			execution_providers_with_options.append((execution_provider,
			{
				'device_id': execution_device_id,
				'cudnn_conv_algo_search': 'EXHAUSTIVE' if use_exhaustive() else 'DEFAULT'
			}))
		elif execution_provider == 'OpenVINOExecutionProvider':
			execution_providers_with_options.append((execution_provider,
			{
				'device_id': execution_device_id,
				'device_type': execution_device_id + '_FP32'
			}))
		elif execution_provider in [ 'DmlExecutionProvider', 'ROCMExecutionProvider' ]:
			execution_providers_with_options.append((execution_provider,
			{
				'device_id': execution_device_id
			}))
		else:
			execution_providers_with_options.append(execution_provider)
	return execution_providers_with_options


def use_exhaustive() -> bool:
=======
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
>>>>>>> origin/master
	execution_devices = detect_static_execution_devices()
	product_names = ('GeForce GTX 1630', 'GeForce GTX 1650', 'GeForce GTX 1660')

	return any(execution_device.get('product').get('name').startswith(product_names) for execution_device in execution_devices)


def run_nvidia_smi() -> subprocess.Popen[bytes]:
<<<<<<< HEAD
	commands = [ 'nvidia-smi', '--query', '--xml-format' ]
=======
	commands = [ shutil.which('nvidia-smi'), '--query', '--xml-format' ]
>>>>>>> origin/master
	return subprocess.Popen(commands, stdout = subprocess.PIPE)


@lru_cache(maxsize = None)
def detect_static_execution_devices() -> List[ExecutionDevice]:
	return detect_execution_devices()


def detect_execution_devices() -> List[ExecutionDevice]:
	execution_devices : List[ExecutionDevice] = []
<<<<<<< HEAD
=======

>>>>>>> origin/master
	try:
		output, _ = run_nvidia_smi().communicate()
		root_element = ElementTree.fromstring(output)
	except Exception:
		root_element = ElementTree.Element('xml')

	for gpu_element in root_element.findall('gpu'):
		execution_devices.append(
		{
<<<<<<< HEAD
			'driver_version': root_element.find('driver_version').text,
			'framework':
			{
				'name': 'CUDA',
				'version': root_element.find('cuda_version').text
=======
			'driver_version': root_element.findtext('driver_version'),
			'framework':
			{
				'name': 'CUDA',
				'version': root_element.findtext('cuda_version')
>>>>>>> origin/master
			},
			'product':
			{
				'vendor': 'NVIDIA',
<<<<<<< HEAD
				'name': gpu_element.find('product_name').text.replace('NVIDIA ', '')
			},
			'video_memory':
			{
				'total': create_value_and_unit(gpu_element.find('fb_memory_usage/total').text),
				'free': create_value_and_unit(gpu_element.find('fb_memory_usage/free').text)
			},
			'utilization':
			{
				'gpu': create_value_and_unit(gpu_element.find('utilization/gpu_util').text),
				'memory': create_value_and_unit(gpu_element.find('utilization/memory_util').text)
			}
		})
	return execution_devices


def create_value_and_unit(text : str) -> ValueAndUnit:
	value, unit = text.split()
	value_and_unit : ValueAndUnit =\
	{
		'value': value,
		'unit': unit
	}

	return value_and_unit
=======
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
>>>>>>> origin/master
