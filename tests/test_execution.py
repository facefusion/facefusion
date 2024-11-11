from facefusion.execution import create_execution_providers, get_execution_provider_set, has_execution_provider


def test_get_execution_provider_set() -> None:
	assert 'cpu' in get_execution_provider_set().keys()


def test_has_execution_provider() -> None:
	assert has_execution_provider('cpu') is True
	assert has_execution_provider('openvino') is False


def test_multiple_execution_providers() -> None:
	execution_providers =\
	[
		('CUDAExecutionProvider',
		{
			'device_id': '1'
		}),
		'CPUExecutionProvider'
	]

	assert create_execution_providers('1', [ 'cpu', 'cuda' ]) == execution_providers
