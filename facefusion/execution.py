import subprocess
import xml.etree.ElementTree as ElementTree
from functools import lru_cache
from typing import Any, List

import onnx
from onnxruntime import InferenceSession, get_available_providers, set_default_logger_severity

from facefusion.choices import execution_provider_set
from facefusion.typing import DownloadSet, ExecutionDevice, ExecutionProviderKey, ExecutionProviderSet, ExecutionProviderValue, InferencePool, ModelInitializer, ValueAndUnit

set_default_logger_severity(3)


def get_execution_provider_choices() -> List[ExecutionProviderKey]:
	return list(get_available_execution_provider_set().keys())


def has_execution_provider(execution_provider_key : ExecutionProviderKey) -> bool:
	return execution_provider_key in get_execution_provider_choices()


def get_available_execution_provider_set() -> ExecutionProviderSet:
	available_execution_providers = get_available_providers()
	available_execution_provider_set : ExecutionProviderSet = {}

	for execution_provider_key, execution_provider_value in execution_provider_set.items():
		if execution_provider_value in available_execution_providers:
			available_execution_provider_set[execution_provider_key] = execution_provider_value
	return available_execution_provider_set


def extract_execution_providers(execution_provider_keys : List[ExecutionProviderKey]) -> List[ExecutionProviderValue]:
	return [ execution_provider_set[execution_provider_key] for execution_provider_key in execution_provider_keys if execution_provider_key in execution_provider_set ]


def create_execution_providers(execution_device_id : str, execution_provider_keys : List[ExecutionProviderKey]) -> List[Any]:
	execution_providers = extract_execution_providers(execution_provider_keys)
	execution_providers_with_options : List[Any] = []

	for execution_provider in execution_providers:
		if execution_provider == 'CUDAExecutionProvider':
			execution_providers_with_options.append((execution_provider,
			{
				'device_id': execution_device_id,
				'cudnn_conv_algo_search': 'EXHAUSTIVE' if use_exhaustive() else 'DEFAULT'
			}))
		elif execution_provider == 'TensorrtExecutionProvider':
			execution_providers_with_options.append((execution_provider,
			{
				'device_id': execution_device_id,
				'trt_engine_cache_enable': True,
				'trt_engine_cache_path': '.caches',
				'trt_timing_cache_enable': True,
				'trt_timing_cache_path': '.caches'
			}))
		elif execution_provider == 'OpenVINOExecutionProvider':
			execution_providers_with_options.append((execution_provider,
			{
				'device_type': 'GPU.' + execution_device_id,
				'precision': 'FP32'
			}))
		elif execution_provider in [ 'DmlExecutionProvider', 'ROCMExecutionProvider' ]:
			execution_providers_with_options.append((execution_provider,
			{
				'device_id': execution_device_id
			}))
		elif execution_provider == 'CoreMLExecutionProvider':
			execution_providers_with_options.append(execution_provider)

	if 'CPUExecutionProvider' in execution_providers:
		execution_providers_with_options.append('CPUExecutionProvider')

	return execution_providers_with_options


def use_exhaustive() -> bool:
	execution_devices = detect_static_execution_devices()
	product_names = ('GeForce GTX 1630', 'GeForce GTX 1650', 'GeForce GTX 1660')

	return any(execution_device.get('product').get('name').startswith(product_names) for execution_device in execution_devices)


def create_inference_session(model_path : str, execution_device_id : str, execution_provider_keys : List[ExecutionProviderKey]) -> InferenceSession:
	providers = create_execution_providers(execution_device_id, execution_provider_keys)
	return InferenceSession(model_path, providers = providers)


def create_inference_pool(model_sources : DownloadSet, execution_device_id : str, execution_provider_keys : List[ExecutionProviderKey]) -> InferencePool:
	inference_pool : InferencePool = {}

	for model_name in model_sources.keys():
		inference_pool[model_name] = create_inference_session(model_sources.get(model_name).get('path'), execution_device_id, execution_provider_keys)
	return inference_pool


@lru_cache(maxsize = None)
def get_static_model_initializer(model_path : str) -> ModelInitializer:
	model = onnx.load(model_path)
	return onnx.numpy_helper.to_array(model.graph.initializer[-1])


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
				'version': root_element.find('cuda_version').text
			},
			'product':
			{
				'vendor': 'NVIDIA',
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
		'value': int(value),
		'unit': str(unit)
	}

	return value_and_unit
