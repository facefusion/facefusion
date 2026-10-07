import pytest

from facefusion import state_manager
from facefusion.download import conditional_download, resolve_download_url
from facefusion.filesystem import resolve_relative_path
from facefusion.model_helper import get_static_model_initializer


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('download_providers', [ 'github' ])

	conditional_download(resolve_relative_path('../.assets/models'),
	[
		resolve_download_url('models-3.0.0', 'inswapper_128.hash'),
		resolve_download_url('models-3.0.0', 'inswapper_128.onnx')
	])


def test_get_static_model_initializer() -> None:
	assert get_static_model_initializer(resolve_relative_path('../.assets/models/inswapper_128.onnx')).shape == (512, 512)
