import numpy
import pytest

from facefusion.download import conditional_download
from facefusion.model_helper import get_static_model_initializer


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download('.assets/models',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/inswapper_128.onnx'
	])


def test_get_static_model_initializer() -> None:
	model_initializer = get_static_model_initializer('.assets/models/inswapper_128.onnx')

	assert model_initializer.shape == (512, 512)
	assert model_initializer.dtype == numpy.float32
	assert get_static_model_initializer('.assets/models/inswapper_128.onnx') is model_initializer
