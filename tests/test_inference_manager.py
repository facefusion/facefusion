from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from onnxruntime import InferenceSession

from facefusion import content_analyser, state_manager
from facefusion.execution import resolve_cache_path
from facefusion.inference_manager import INFERENCE_POOL_SET, get_inference_pool, resolve_static_inference_providers
from facefusion.session_context import clear_session_id, resolve_step_id, set_session_id


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github' ])


def test_get_inference_pool() -> None:
	model_names = [ 'nsfw_1', 'nsfw_2', 'nsfw_3' ]
	_, model_source_set = content_analyser.collect_model_downloads()

	set_session_id('session-a')
	state_manager.set_item('execution_device_ids', [ 0 ])
	state_manager.set_item('execution_providers', [ 'cpu' ])
	session_a_inference_pool = get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

	assert isinstance(session_a_inference_pool.get('nsfw_1'), InferenceSession)

	set_session_id('session-b')
	state_manager.set_item('execution_device_ids', [ 0 ])
	state_manager.set_item('execution_providers', [ 'cpu' ])
	session_b_inference_pool = get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

	assert isinstance(session_b_inference_pool.get('nsfw_1'), InferenceSession)
	assert session_a_inference_pool.get('nsfw_1') is session_b_inference_pool.get('nsfw_1')
	assert 'facefusion.content_analyser.nsfw_1.nsfw_2.nsfw_3.0.cpu' in INFERENCE_POOL_SET.get('session-b')

	with patch('facefusion.inference_manager.has_execution_provider', Mock(return_value = True)):
		with patch('facefusion.inference_manager.get_onnxruntime_version', Mock(return_value = (1, 25, 0))):
			set_session_id('session-c')
			state_manager.set_item('execution_device_ids', [ 0 ])
			state_manager.set_item('execution_providers', [ 'cpu' ])
			session_c_inference_pool = get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

			assert isinstance(session_c_inference_pool.get('nsfw_1'), InferenceSession)
			assert (session_a_inference_pool.get('nsfw_1') is session_c_inference_pool.get('nsfw_1')) is False

			step_session_id = resolve_step_id('session-c')
			set_session_id(step_session_id)
			state_manager.set_item('execution_device_ids', [ 0 ])
			state_manager.set_item('execution_providers', [ 'cpu' ])
			step_inference_pool = get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

			assert step_inference_pool.get('nsfw_1') is session_c_inference_pool.get('nsfw_1')
			assert INFERENCE_POOL_SET.get(step_session_id) is None

	clear_session_id()


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
