import os
from unittest.mock import patch

import onnxruntime

from facefusion.execution import create_inference_providers, get_available_execution_providers, get_onnxruntime_version, has_execution_provider, resolve_cache_path, resolve_cudnn_conv_algo_search, resolve_openvino_device_type


def test_get_onnxruntime_version() -> None:
	assert '.'.join(map(str, get_onnxruntime_version())) == onnxruntime.get_version_string()


def test_has_execution_provider() -> None:
	assert has_execution_provider('cpu') is True
	assert has_execution_provider('openvino') is False


def test_get_available_execution_providers() -> None:
	assert 'cpu' in get_available_execution_providers()
	assert get_available_execution_providers()[-1] == 'cpu'


def test_create_inference_providers() -> None:
	inference_providers =\
	[
		('CUDAExecutionProvider',
		{
			'device_id': 1,
			'cudnn_conv_algo_search': 'EXHAUSTIVE'
		}),
		'CPUExecutionProvider'
	]

	assert create_inference_providers(1, [ 'cpu', 'cuda' ]) == inference_providers

	inference_providers =\
	[
		('TensorrtExecutionProvider',
		{
			'device_id': 1,
			'trt_engine_cache_enable': True,
			'trt_engine_cache_path': resolve_cache_path(),
			'trt_timing_cache_enable': True,
			'trt_timing_cache_path': resolve_cache_path(),
			'trt_builder_optimization_level': 4
		}),
		('MIGraphXExecutionProvider',
		{
			'device_id': 1,
			'migraphx_model_cache_dir': resolve_cache_path()
		}),
		('CoreMLExecutionProvider',
		{
			'SpecializationStrategy': 'FastPrediction',
			'ModelCacheDirectory': resolve_cache_path()
		}),
		('OpenVINOExecutionProvider',
		{
			'device_type': 'GPU.1',
			'precision': 'FP32'
		}),
		('QNNExecutionProvider',
		{
			'device_id': 1,
			'backend_type': 'htp'
		}),
		('DmlExecutionProvider',
		{
			'device_id': 1
		})
	]

	assert create_inference_providers(1, [ 'tensorrt', 'migraphx', 'coreml', 'openvino', 'qnn', 'directml' ]) == inference_providers
	assert create_inference_providers(0, []) == []


def test_resolve_cache_path() -> None:
	assert resolve_cache_path() == os.path.join('.caches', onnxruntime.get_version_string())


def test_resolve_cudnn_conv_algo_search() -> None:
	graphic_devices =\
	[
		{
			'product':
			{
				'vendor': 'NVIDIA',
				'name': 'GeForce GTX 1650 SUPER'
			}
		}
	]

	with patch('facefusion.execution.detect_graphic_devices', return_value = graphic_devices):
		assert resolve_cudnn_conv_algo_search([ 'cuda' ]) == 'DEFAULT'

	assert resolve_cudnn_conv_algo_search([ 'cpu' ]) == 'EXHAUSTIVE'


def test_resolve_openvino_device_type() -> None:
	assert resolve_openvino_device_type(0) == 'GPU'
	assert resolve_openvino_device_type(1) == 'GPU.1'
