from facefusion.execution import encode_execution_providers, decode_execution_providers, apply_execution_provider_options


def test_encode_execution_providers() -> None:
	assert encode_execution_providers([ 'CPUExecutionProvider' ]) == [ 'cpu' ]


def test_decode_execution_providers() -> None:
	assert decode_execution_providers([ 'cpu' ]) == [ 'CPUExecutionProvider' ]


def test_multiple_execution_providers() -> None:
	execution_provider_with_options =\
	[
		'CPUExecutionProvider',
		('CUDAExecutionProvider',
		{
			'cudnn_conv_algo_search': 'DEFAULT'
		})
	]
	assert apply_execution_provider_options([ 'CPUExecutionProvider', 'CUDAExecutionProvider' ]) == execution_provider_with_options
