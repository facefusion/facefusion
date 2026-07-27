from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from onnxruntime import InferenceSession

from facefusion import content_analyser, state_manager
from facefusion.execution import resolve_cache_path
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


@pytest.fixture
def override_module() -> SimpleNamespace:
	return SimpleNamespace(override_inference_providers = Mock(return_value = [ ('CoreMLExecutionProvider', { 'ModelFormat': 'MLProgram' }) ]))


@pytest.fixture
def adjust_module() -> SimpleNamespace:
	return SimpleNamespace(adjust_inference_providers = Mock(return_value = [ ('CoreMLExecutionProvider', { 'ModelFormat': 'MLProgram' }) ]))


def test_resolve_static_inference_providers(override_module : SimpleNamespace, adjust_module : SimpleNamespace) -> None:
	state_manager.init_item('execution_providers', ['coreml'])
	resolve_static_inference_providers.cache_clear()

	with patch('facefusion.inference_manager.importlib', Mock(import_module = Mock(return_value = override_module))):
		assert resolve_static_inference_providers('override_module', 0) == [ ('CoreMLExecutionProvider', { 'ModelFormat': 'MLProgram' }) ]

	with patch('facefusion.inference_manager.importlib', Mock(import_module = Mock(return_value = adjust_module))):
		assert resolve_static_inference_providers('adjust_module', 0) == [ ('CoreMLExecutionProvider', { 'SpecializationStrategy': 'FastPrediction', 'ModelCacheDirectory': resolve_cache_path(), 'ModelFormat': 'MLProgram' }) ]

	assert resolve_static_inference_providers('test', 0) == [ ('CoreMLExecutionProvider', { 'SpecializationStrategy': 'FastPrediction', 'ModelCacheDirectory': resolve_cache_path() }) ]
