from typing import Any, List
import onnxruntime


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
				'cudnn_conv_algo_search': 'DEFAULT'
			}))
		else:
			execution_providers_with_options.append(execution_provider)
	return execution_providers_with_options


def map_torch_backend(execution_providers : List[str]) -> str:
	if 'CoreMLExecutionProvider' in execution_providers:
		return 'mps'
	if 'CUDAExecutionProvider' in execution_providers or 'ROCMExecutionProvider' in execution_providers :
		return 'cuda'
	if 'OpenVINOExecutionProvider' in execution_providers:
		return 'mkl'
	return 'cpu'
