from facefusion.execution import encode_execution_providers, decode_execution_providers, has_execution_provider, apply_execution_provider_options


def test_encode_execution_providers() -> None:
	assert encode_execution_providers([ 'CPUExecutionProvider' ]) == [ 'cpu' ]


def test_decode_execution_providers() -> None:
	assert decode_execution_providers([ 'cpu' ]) == [ 'CPUExecutionProvider' ]


def test_has_execution_provider() -> None:
	assert has_execution_provider('CPUExecutionProvider') is True
	assert has_execution_provider('InvalidExecutionProvider') is False


def test_multiple_execution_providers() -> None:
	execution_provider_with_options =\
	[
		'CPUExecutionProvider',
		('CUDAExecutionProvider',
		{
			'device_id': '1',
			'cudnn_conv_algo_search': 'DEFAULT'
		})
	]
	assert apply_execution_provider_options('1', [ 'CPUExecutionProvider', 'CUDAExecutionProvider' ]) == execution_provider_with_options
