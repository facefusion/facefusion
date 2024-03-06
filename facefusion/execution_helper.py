from typing import Any, List
import onnxruntime

from facefusion.devices import detect_static_cuda_devices


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
	cuda_devices = detect_static_cuda_devices()
	product_names = [ 'geforce gtx 1650', 'geforce gtx 1660' ]

	return any(cuda_device.get('product').get('name') in product_names for cuda_device in cuda_devices)
