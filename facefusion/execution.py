from typing import List, Any
from functools import lru_cache
import subprocess
import xml.etree.ElementTree as ElementTree
import onnxruntime

from facefusion.typing import ExecutionDevice, ValueAndUnit


def encode_execution_providers(execution_providers : List[str]) -> List[str]:
	return [ execution_provider.replace('ExecutionProvider', '').lower() for execution_provider in execution_providers ]


def decode_execution_providers(execution_providers: List[str]) -> List[str]:
	available_execution_providers = onnxruntime.get_available_providers()
	encoded_execution_providers = encode_execution_providers(available_execution_providers)

	return [ execution_provider for execution_provider, encoded_execution_provider in zip(available_execution_providers, encoded_execution_providers) if any(execution_provider in encoded_execution_provider for execution_provider in execution_providers) ]


def apply_execution_provider_options(execution_providers: List[str]) -> List[Any]:
	execution_providers_with_options : List[Any] = []

	for execution_provider in execution_providers:
		if execution_provider == 'CUDAExecutionProvider':
			execution_providers_with_options.append((execution_provider,
			{
				'cudnn_conv_algo_search': 'EXHAUSTIVE' if use_exhaustive() else 'DEFAULT'
			}))
		else:
			execution_providers_with_options.append(execution_provider)
	return execution_providers_with_options


def use_exhaustive() -> bool:
	execution_devices = detect_static_execution_devices()
	product_names = ('GeForce GTX 1630', 'GeForce GTX 1650', 'GeForce GTX 1660')

	return any(execution_device.get('product').get('name').startswith(product_names) for execution_device in execution_devices)


def run_nvidia_smi() -> subprocess.Popen[bytes]:
	commands = [ 'nvidia-smi', '--query', '--xml-format' ]
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
			'driver_version': root_element.find('driver_version').text,
			'framework':
			{
				'name': 'CUDA',
				'version': root_element.find('cuda_version').text,
			},
			'product':
			{
				'vendor': 'NVIDIA',
				'name': gpu_element.find('product_name').text.replace('NVIDIA ', ''),
				'architecture': gpu_element.find('product_architecture').text,
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
