from types import SimpleNamespace
from typing import Iterator
from unittest.mock import Mock, patch

import pytest
from onnxruntime import InferenceSession

from facefusion import content_analyser, session_context, state_manager, store_creator
from facefusion.execution import resolve_cache_path
from facefusion.inference_manager import INFERENCE_POOL_STORE, clear, get_inference_pool, init, resolve_static_inference_providers


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github' ])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = session_context.resolve_local_id()

	for session_id in list(INFERENCE_POOL_STORE.get('content_set').keys()):
		store_creator.delete_content(INFERENCE_POOL_STORE, session_id)

	session_context.set_session_id(local_id)
	init()

	yield

	session_context.set_session_id(local_id)


def test_init() -> None:
	local_id = session_context.resolve_local_id()
	model_names = [ 'nsfw_1', 'nsfw_2', 'nsfw_3' ]
	_, model_source_set = content_analyser.collect_model_downloads()

	local_inference_pool = get_inference_pool('facefusion.content_analyser', model_names, model_source_set)
	session_context.set_session_id('session-a')
	state_manager.init()
	init()
	session_inference_pool = get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

	assert session_inference_pool.get('nsfw_1') is local_inference_pool.get('nsfw_1')

	session_context.set_session_id(local_id)

	assert get_inference_pool('facefusion.content_analyser', model_names, model_source_set) is local_inference_pool


def test_get_inference_pool() -> None:
	model_names = [ 'nsfw_1', 'nsfw_2', 'nsfw_3' ]
	_, model_source_set = content_analyser.collect_model_downloads()

	with patch('facefusion.inference_manager.has_execution_provider', return_value = True):
		with patch('facefusion.inference_manager.get_onnxruntime_version', return_value = (1, 26, 0)):
			session_context.set_session_id('session-a')
			state_manager.init()
			init()
			session_a_inference_pool = get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

			assert isinstance(session_a_inference_pool.get('nsfw_1'), InferenceSession)

			session_context.set_session_id('session-b')
			state_manager.init()
			init()
			session_b_inference_pool = get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

			assert isinstance(session_b_inference_pool.get('nsfw_1'), InferenceSession)
			assert not session_a_inference_pool.get('nsfw_1') is session_b_inference_pool.get('nsfw_1')

	with patch('facefusion.inference_manager.get_onnxruntime_version', return_value = (1, 24, 4)):
		session_context.set_session_id('session-c')
		state_manager.init()
		init()
		session_c_inference_pool = get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

		assert isinstance(session_c_inference_pool.get('nsfw_1'), InferenceSession)
		assert session_c_inference_pool.get('nsfw_1') is session_a_inference_pool.get('nsfw_1')


def test_clear() -> None:
	model_names = [ 'nsfw_1', 'nsfw_2', 'nsfw_3' ]
	_, model_source_set = content_analyser.collect_model_downloads()

	session_context.set_session_id('session-a')
	state_manager.init()
	init()
	get_inference_pool('facefusion.content_analyser', model_names, model_source_set)
	clear()

	assert store_creator.get_content(INFERENCE_POOL_STORE, 'session-a') == {}


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
