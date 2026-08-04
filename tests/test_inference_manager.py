from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from onnxruntime import InferenceSession

from facefusion import content_analyser, state_manager
from facefusion.execution import resolve_cache_path
from facefusion.inference_manager import get_inference_pool, resolve_static_inference_providers


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github' ])


def test_get_inference_pool() -> None:
	model_names = [ 'nsfw_1', 'nsfw_2', 'nsfw_3' ]
	_, model_source_set = content_analyser.collect_model_downloads()

	with patch('facefusion.inference_manager.has_execution_provider', return_value = True):
		with patch('facefusion.inference_manager.get_onnxruntime_version', return_value = (1, 26, 0)):

			with patch('facefusion.inference_manager.detect_app_context', return_value = 'cli'):
				cli_inference_pool = get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

				assert isinstance(cli_inference_pool.get('nsfw_1'), InferenceSession)

			with patch('facefusion.inference_manager.detect_app_context', return_value = 'ui'):
				ui_inference_pool = get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

				assert isinstance(ui_inference_pool.get('nsfw_1'), InferenceSession)

			assert not (cli_inference_pool.get('nsfw_1') is ui_inference_pool.get('nsfw_1'))

	with patch('facefusion.inference_manager.get_onnxruntime_version', return_value = (1, 24, 4)):

		with patch('facefusion.inference_manager.detect_app_context', return_value = 'ui'):
			ui_inference_pool = get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

			assert isinstance(ui_inference_pool.get('nsfw_1'), InferenceSession)

	assert cli_inference_pool.get('nsfw_1') is ui_inference_pool.get('nsfw_1')


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
		inference_providers = resolve_static_inference_providers('override_module', 0)

		assert inference_providers == [ ('CoreMLExecutionProvider', { 'ModelFormat': 'MLProgram' }) ]

	with patch('facefusion.inference_manager.importlib', Mock(import_module = Mock(return_value = adjust_module))):
		inference_providers = resolve_static_inference_providers('adjust_module', 0)

		assert inference_providers == [ ('CoreMLExecutionProvider', { 'SpecializationStrategy': 'FastPrediction', 'ModelCacheDirectory': resolve_cache_path(), 'ModelFormat': 'MLProgram' }) ]

	inference_providers = resolve_static_inference_providers('test', 0)

	assert inference_providers == [ ('CoreMLExecutionProvider', { 'SpecializationStrategy': 'FastPrediction', 'ModelCacheDirectory': resolve_cache_path() }) ]
