import os
import shutil
import subprocess

from functools import lru_cache
from typing import List, Optional
import pynvml
import onnxruntime

import facefusion.choices
from facefusion.filesystem import create_directory, is_directory
from facefusion.types import ExecutionDevice, ExecutionProvider, InferenceOptionSet, InferenceProvider, ValueAndUnit

onnxruntime.set_default_logger_severity(3)


def has_execution_provider(execution_provider : ExecutionProvider) -> bool:
	return execution_provider in get_available_execution_providers()


def get_available_execution_providers() -> List[ExecutionProvider]:
	inference_session_providers = onnxruntime.get_available_providers()
	available_execution_providers : List[ExecutionProvider] = []

	for execution_provider, execution_provider_value in facefusion.choices.execution_provider_set.items():
		if execution_provider_value in inference_session_providers:
			index = facefusion.choices.execution_providers.index(execution_provider)
			available_execution_providers.insert(index, execution_provider)

	return available_execution_providers


def create_inference_providers(execution_device_id : int, execution_providers : List[ExecutionProvider]) -> List[InferenceProvider]:
	inference_providers : List[InferenceProvider] = []
	cache_path = resolve_cache_path()

	for execution_provider in execution_providers:
		if execution_provider == 'cuda':
			inference_providers.append((facefusion.choices.execution_provider_set.get(execution_provider),
			{
				'device_id': execution_device_id,
				'cudnn_conv_algo_search': resolve_cudnn_conv_algo_search()
			}))

		if execution_provider == 'tensorrt':
			inference_option_set : InferenceOptionSet =\
			{
				'device_id': execution_device_id
			}
			if is_directory(cache_path) or create_directory(cache_path):
				inference_option_set.update(
				{
					'trt_engine_cache_enable': True,
					'trt_engine_cache_path': cache_path,
					'trt_timing_cache_enable': True,
					'trt_timing_cache_path': cache_path,
					'trt_builder_optimization_level': 4
				})
			inference_providers.append((facefusion.choices.execution_provider_set.get(execution_provider), inference_option_set))

		if execution_provider in [ 'directml', 'rocm' ]:
			inference_providers.append((facefusion.choices.execution_provider_set.get(execution_provider),
			{
				'device_id': execution_device_id
			}))

		if execution_provider == 'migraphx':
			inference_option_set =\
			{
				'device_id': execution_device_id
			}
			if is_directory(cache_path) or create_directory(cache_path):
				inference_option_set.update(
				{
					'migraphx_model_cache_dir': cache_path
				})
			inference_providers.append((facefusion.choices.execution_provider_set.get(execution_provider), inference_option_set))

		if execution_provider == 'coreml':
			inference_option_set =\
			{
				'SpecializationStrategy': 'FastPrediction'
			}
			if is_directory(cache_path) or create_directory(cache_path):
				inference_option_set.update(
				{
					'ModelCacheDirectory': cache_path
				})
			inference_providers.append((facefusion.choices.execution_provider_set.get(execution_provider), inference_option_set))

		if execution_provider == 'openvino':
			inference_providers.append((facefusion.choices.execution_provider_set.get(execution_provider),
			{
				'device_type': resolve_openvino_device_type(execution_device_id),
				'precision': 'FP32'
			}))

		if execution_provider == 'qnn':
			inference_providers.append((facefusion.choices.execution_provider_set.get(execution_provider),
			{
				'device_id': execution_device_id,
				'backend_type': 'htp'
			}))

	if 'cpu' in execution_providers:
		inference_providers.append(facefusion.choices.execution_provider_set.get('cpu'))

	return inference_providers


def resolve_cache_path() -> str:
	return os.path.join('.caches', onnxruntime.get_version_string())


def resolve_cudnn_conv_algo_search() -> str:
	execution_devices = detect_static_execution_devices()
	product_names = ('GeForce GTX 1630', 'GeForce GTX 1650', 'GeForce GTX 1660')

	for execution_device in execution_devices:
		if execution_device.get('product').get('name').startswith(product_names):
			return 'DEFAULT'

	return 'EXHAUSTIVE'


def resolve_openvino_device_type(execution_device_id : int) -> str:
	if execution_device_id == 0:
		return 'GPU'
	return 'GPU.' + str(execution_device_id)
