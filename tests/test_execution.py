from facefusion.execution import get_execution_provider_choices, has_execution_provider, apply_execution_provider_options


def test_get_execution_provider_choices() -> None:
	assert 'cpu' in get_execution_provider_choices()


def test_has_execution_provider() -> None:
	assert has_execution_provider('cpu') is True
	assert has_execution_provider('openvino') is False


def test_multiple_execution_providers() -> None:
	execution_provider_with_options =\
	[
		('CUDAExecutionProvider',
		{
			'device_id': '1',
			'cudnn_conv_algo_search': 'DEFAULT'
		}),
		'CPUExecutionProvider'
	]

	assert apply_execution_provider_options('1', [ 'cpu', 'cuda' ]) == execution_provider_with_options
