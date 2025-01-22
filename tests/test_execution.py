from facefusion.execution import create_inference_session_providers, get_available_execution_providers, has_execution_provider


def test_has_execution_provider() -> None:
	assert has_execution_provider('cpu') is True
	assert has_execution_provider('openvino') is False


def test_get_available_execution_providers() -> None:
	assert 'cpu' in get_available_execution_providers()


def test_create_inference_session_providers() -> None:
	inference_session_providers =\
	[
		('CUDAExecutionProvider',
		{
			'device_id': '1',
			'cudnn_conv_algo_search': 'EXHAUSTIVE'
		}),
		'CPUExecutionProvider'
	]

	assert create_inference_session_providers('1', [ 'cpu', 'cuda' ]) == inference_session_providers
