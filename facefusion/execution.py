from typing import List

from onnxruntime import get_available_providers, set_default_logger_severity

import facefusion.choices
from facefusion.system import detect_static_graphic_devices
from facefusion.types import ExecutionProvider, InferenceSessionProvider

set_default_logger_severity(3)


def has_execution_provider(execution_provider : ExecutionProvider) -> bool:
	return execution_provider in get_available_execution_providers()


def get_available_execution_providers() -> List[ExecutionProvider]:
	inference_session_providers = get_available_providers()
	available_execution_providers : List[ExecutionProvider] = []

	for execution_provider, execution_provider_value in facefusion.choices.execution_provider_set.items():
		if execution_provider_value in inference_session_providers:
			index = facefusion.choices.execution_providers.index(execution_provider)
			available_execution_providers.insert(index, execution_provider)

	return available_execution_providers


def create_inference_session_providers(execution_device_id : int, execution_providers : List[ExecutionProvider]) -> List[InferenceSessionProvider]:
	inference_session_providers : List[InferenceSessionProvider] = []

	for execution_provider in execution_providers:
		if execution_provider == 'cuda':
			inference_session_providers.append((facefusion.choices.execution_provider_set.get(execution_provider),
			{
				'device_id': execution_device_id,
				'cudnn_conv_algo_search': resolve_cudnn_conv_algo_search()
			}))
		if execution_provider == 'tensorrt':
			inference_session_providers.append((facefusion.choices.execution_provider_set.get(execution_provider),
			{
				'device_id': execution_device_id,
				'trt_engine_cache_enable': True,
				'trt_engine_cache_path': '.caches',
				'trt_timing_cache_enable': True,
				'trt_timing_cache_path': '.caches',
				'trt_builder_optimization_level': 5
			}))
		if execution_provider in [ 'directml', 'rocm' ]:
			inference_session_providers.append((facefusion.choices.execution_provider_set.get(execution_provider),
			{
				'device_id': execution_device_id
			}))
		if execution_provider == 'migraphx':
			inference_session_providers.append((facefusion.choices.execution_provider_set.get(execution_provider),
			{
				'device_id': execution_device_id,
				'migraphx_model_cache_dir': '.caches'
			}))
		if execution_provider == 'openvino':
			inference_session_providers.append((facefusion.choices.execution_provider_set.get(execution_provider),
			{
				'device_type': resolve_openvino_device_type(execution_device_id),
				'precision': 'FP32'
			}))
		if execution_provider == 'coreml':
			inference_session_providers.append((facefusion.choices.execution_provider_set.get(execution_provider),
			{
				'SpecializationStrategy': 'FastPrediction',
				'ModelCacheDirectory': '.caches'
			}))

	if 'cpu' in execution_providers:
		inference_session_providers.append(facefusion.choices.execution_provider_set.get('cpu'))

	return inference_session_providers


def resolve_cudnn_conv_algo_search() -> str:
	execution_devices = detect_static_graphic_devices()
	product_names = ('GeForce GTX 1630', 'GeForce GTX 1650', 'GeForce GTX 1660')

	for execution_device in execution_devices:
		if execution_device.get('product').get('name').startswith(product_names):
			return 'DEFAULT'

	return 'EXHAUSTIVE'


def resolve_openvino_device_type(execution_device_id : int) -> str:
	if execution_device_id == 0:
		return 'GPU'
	return 'GPU.' + str(execution_device_id)
