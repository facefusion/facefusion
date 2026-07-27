from types import SimpleNamespace
from unittest.mock import patch

import pytest
from onnxruntime import InferenceSession

from facefusion import content_analyser, state_manager
from facefusion.inference_manager import INFERENCE_POOL_SET, get_inference_pool, resolve_static_inference_providers


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github' ])


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


def test_resolve_static_inference_providers() -> None:
	resolve_static_inference_providers.cache_clear()
	override_module = SimpleNamespace(override_inference_providers = lambda: [ ('OverrideExecutionProvider', {}) ])
	adjust_module = SimpleNamespace(adjust_inference_providers = lambda: [ ('CoreMLExecutionProvider', { 'ModelFormat': 'MLProgram' }) ])
	default_module = SimpleNamespace()

	with patch.dict('sys.modules', { 'test_override': override_module, 'test_adjust': adjust_module, 'test_default': default_module }),\
		patch('facefusion.inference_manager.create_inference_providers', side_effect = lambda *args: [ ('CoreMLExecutionProvider', { 'SpecializationStrategy': 'FastPrediction' }) ]):
		assert resolve_static_inference_providers('test_override', 0) == [ ('OverrideExecutionProvider', {}) ]
		assert resolve_static_inference_providers('test_adjust', 0) == [ ('CoreMLExecutionProvider', { 'SpecializationStrategy': 'FastPrediction', 'ModelFormat': 'MLProgram' }) ]
		assert resolve_static_inference_providers('test_default', 0) == [ ('CoreMLExecutionProvider', { 'SpecializationStrategy': 'FastPrediction' }) ]
