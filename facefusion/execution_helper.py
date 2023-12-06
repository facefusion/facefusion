from typing import List
import onnxruntime


def encode_execution_providers(execution_providers : List[str]) -> List[str]:
	return [ execution_provider.replace('ExecutionProvider', '').lower() for execution_provider in execution_providers ]


def decode_execution_providers(execution_providers: List[str]) -> List[str]:
	available_execution_providers = onnxruntime.get_available_providers()
	encoded_execution_providers = encode_execution_providers(available_execution_providers)
	return [ execution_provider for execution_provider, encoded_execution_provider in zip(available_execution_providers, encoded_execution_providers) if any(execution_provider in encoded_execution_provider for execution_provider in execution_providers) ]


def map_device(execution_providers : List[str]) -> str:
	if 'CoreMLExecutionProvider' in execution_providers:
		return 'mps'
	if 'CUDAExecutionProvider' in execution_providers or 'ROCMExecutionProvider' in execution_providers :
		return 'cuda'
	if 'OpenVINOExecutionProvider' in execution_providers:
		return 'mkl'
	return 'cpu'
