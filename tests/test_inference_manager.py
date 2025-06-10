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
	model_names = [ 'yolo_11m', 'marqo', 'freepik' ]
	_, model_source_set = content_analyser.collect_model_downloads()

	with patch('facefusion.inference_manager.detect_app_context', return_value = 'cli'):
		get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

		assert isinstance(INFERENCE_POOL_SET.get('cli').get('facefusion.content_analyser.yolo_11m.marqo.freepik.0.cpu').get('yolo_11m'), InferenceSession)

	with patch('facefusion.inference_manager.detect_app_context', return_value = 'ui'):
		get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

		assert isinstance(INFERENCE_POOL_SET.get('cli').get('facefusion.content_analyser.yolo_11m.marqo.freepik.0.cpu').get('yolo_11m'), InferenceSession)

	assert INFERENCE_POOL_SET.get('cli').get('facefusion.content_analyser.yolo_11m.marqo.freepik.0.cpu').get('yolo_11m') == INFERENCE_POOL_SET.get('ui').get('facefusion.content_analyser.yolo_11m.marqo.freepik.0.cpu').get('yolo_11m')
