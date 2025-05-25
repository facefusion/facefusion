from unittest.mock import patch

import pytest
from onnxruntime import InferenceSession

from testingss import content_analyser, state_manager
from testingss.inference_manager import INFERENCE_POOL_SET, get_inference_pool


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('execution_device_id', '0')
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github' ])
	content_analyser.pre_check()


def test_get_inference_pool() -> None:
	model_names = [ 'yolo_nsfw' ]
	model_source_set = content_analyser.get_model_options().get('sources')

	with patch('testingss.inference_manager.detect_app_context', return_value = 'cli'):
		get_inference_pool('testingss.content_analyser', model_names, model_source_set)

		assert isinstance(INFERENCE_POOL_SET.get('cli').get('testingss.content_analyser.yolo_nsfw.0.cpu').get('content_analyser'), InferenceSession)

	with patch('testingss.inference_manager.detect_app_context', return_value = 'ui'):
		get_inference_pool('testingss.content_analyser', model_names, model_source_set)

		assert isinstance(INFERENCE_POOL_SET.get('ui').get('testingss.content_analyser.yolo_nsfw.0.cpu').get('content_analyser'), InferenceSession)

	assert INFERENCE_POOL_SET.get('cli').get('testingss.content_analyser.yolo_nsfw.0.cpu').get('content_analyser') == INFERENCE_POOL_SET.get('ui').get('testingss.content_analyser.yolo_nsfw.0.cpu').get('content_analyser')
