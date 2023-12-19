from facefusion.execution_helper import encode_execution_providers, decode_execution_providers


def test_encode_execution_providers() -> None:
	assert encode_execution_providers([ 'CPUExecutionProvider' ]) == [ 'cpu' ]


def test_decode_execution_providers() -> None:
	assert decode_execution_providers([ 'cpu' ]) == [ 'CPUExecutionProvider' ]
