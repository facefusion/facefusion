from facefusion.execution import create_inference_execution_providers, get_available_execution_providers, has_execution_provider


def test_has_execution_provider() -> None:
	assert has_execution_provider('cpu') is True
	assert has_execution_provider('openvino') is False


def test_get_available_execution_providers() -> None:
	assert 'cpu' in get_available_execution_providers()


def test_create_inference_execution_providers() -> None:
	execution_providers =\
	[
		('CUDAExecutionProvider',
		{
			'device_id': '1',
			'cudnn_conv_algo_search': 'EXHAUSTIVE'
		}),
		'CPUExecutionProvider'
	]

	assert create_inference_execution_providers('1', [ 'cpu', 'cuda' ]) == execution_providers
