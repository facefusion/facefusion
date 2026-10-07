import pytest

from facefusion import state_manager
from facefusion.download import conditional_download, resolve_download_url
from facefusion.filesystem import resolve_relative_path
from facefusion.hash_helper import create_hash, get_hash_path, validate_hash


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('download_providers', [ 'github' ])

	conditional_download(resolve_relative_path('../.assets/models'),
	[
		resolve_download_url('models-3.4.0', 'yunet_2023_mar.hash'),
		resolve_download_url('models-3.4.0', 'yunet_2023_mar.onnx')
	])


def test_create_hash() -> None:
	assert create_hash(bytes()) == '00000000'
	assert create_hash('facefusion'.encode()) == '6afd0aae'


def test_validate_hash() -> None:
	validate_path = resolve_relative_path('../.assets/models/yunet_2023_mar.onnx')
	hash_path = resolve_relative_path('../.assets/models/yunet_2023_mar.hash')

	assert validate_hash(validate_path) is True
	assert validate_hash(hash_path) is False
	assert validate_hash('invalid') is False


def test_get_hash_path() -> None:
	validate_path = resolve_relative_path('../.assets/models/yunet_2023_mar.onnx')
	hash_path = resolve_relative_path('../.assets/models/yunet_2023_mar.hash')

	assert get_hash_path(validate_path) == hash_path
	assert get_hash_path(resolve_relative_path('../.assets/models')) is None
	assert get_hash_path('invalid') is None
