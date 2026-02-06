from functools import lru_cache
from typing import List

import pynvml
from aitop.core.gpu import GPUMonitorFactory
from onnxruntime import get_available_providers, set_default_logger_severity

import facefusion.choices
from facefusion.types import ExecutionDevice, ExecutionProvider, InferenceSessionProvider

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


def resolve_cuda_driver_version(cuda_driver_version : int) -> str:
	return '{}.{}'.format(cuda_driver_version // 1000, (cuda_driver_version % 1000) // 10)


@lru_cache()
def detect_static_execution_devices() -> List[ExecutionDevice]:
	return detect_execution_devices()


def detect_execution_devices() -> List[ExecutionDevice]:
	execution_devices : List[ExecutionDevice] = []

	try:
		monitors = GPUMonitorFactory.create_monitors()

		for monitor in monitors:
			quick_metrics = monitor.get_quick_metrics()

			pynvml.nvmlInit()

			for device_id, metrics in quick_metrics.items():
				handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
				product_name = pynvml.nvmlDeviceGetName(handle)
				driver_version = pynvml.nvmlSystemGetDriverVersion()
				cuda_driver_version = resolve_cuda_driver_version(pynvml.nvmlSystemGetCudaDriverVersion())
				temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
				memory_total_mib = int(metrics.get('memory_total'))
				memory_used_mib = int(metrics.get('memory_used'))
				memory_free_mib = memory_total_mib - memory_used_mib

				execution_devices.append(
				{
					'driver_version': driver_version,
					'framework':
					{
						'name': 'CUDA',
						'version': cuda_driver_version
					},
					'product':
					{
						'vendor': 'NVIDIA',
						'name': product_name.replace('NVIDIA', '').strip()
					},
					'video_memory':
					{
						'total':
						{
							'value': memory_total_mib,
							'unit': 'MiB'
						},
						'free':
						{
							'value': memory_free_mib,
							'unit': 'MiB'
						}
					},
					'temperature':
					{
						'gpu':
						{
							'value': int(temperature),
							'unit': 'C'
						},
						'memory': None
					},
					'utilization':
					{
						'gpu':
						{
							'value': int(metrics.get('utilization')),
							'unit': '%'
						},
						'memory':
						{
							'value': int(metrics.get('memory_percent')),
							'unit': '%'
						}
					}
				})

			pynvml.nvmlShutdown()
	except Exception:
		pass

	return execution_devices
