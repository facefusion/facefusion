from unittest.mock import patch

import pytest
from onnxruntime import InferenceSession

from facefusion import content_analyser, state_manager
from facefusion.inference_manager import INFERENCE_POOL_SET, get_inference_pool


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('execution_device_id', '0')
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github' ])
	content_analyser.pre_check()


def test_get_inference_pool() -> None:
	model_names = [ 'nsfw_1', 'nsfw_2', 'nsfw_3' ]
	_, model_source_set = content_analyser.collect_model_downloads()

	with patch('facefusion.inference_manager.detect_app_context', return_value = 'cli'):
		get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

		assert isinstance(INFERENCE_POOL_SET.get('cli').get('facefusion.content_analyser.nsfw_1.nsfw_2.nsfw_3.0.cpu').get('nsfw_1'), InferenceSession)

	with patch('facefusion.inference_manager.detect_app_context', return_value = 'ui'):
		get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

		assert isinstance(INFERENCE_POOL_SET.get('cli').get('facefusion.content_analyser.nsfw_1.nsfw_2.nsfw_3.0.cpu').get('nsfw_1'), InferenceSession)

	assert INFERENCE_POOL_SET.get('cli').get('facefusion.content_analyser.nsfw_1.nsfw_2.nsfw_3.0.cpu').get('nsfw_1') == INFERENCE_POOL_SET.get('ui').get('facefusion.content_analyser.nsfw_1.nsfw_2.nsfw_3.0.cpu').get('nsfw_1')
