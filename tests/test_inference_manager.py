from types import SimpleNamespace
from typing import Iterator, Tuple
from unittest.mock import Mock, patch

import pytest
from onnxruntime import InferenceSession

from facefusion import content_analyser, session_context, session_manager, state_manager, store_creator
from facefusion.execution import resolve_cache_path
from facefusion.inference_manager import INFERENCE_POOL_STORE, clear, clear_inference_pool, create_inference_pool, create_inference_session, destroy, find_inference_pool, get_inference_context, get_inference_pool, init, resolve_static_inference_providers


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


@pytest.mark.parametrize('onnxruntime_version, is_shared',
[
	((1, 25, 1), True),
	((1, 26, 0), False),
	((1, 27, 0), False),
	((1, 28, 0), False),
	((1, 29, 0), True)
])
def test_get_inference_pool(onnxruntime_version : Tuple[int, int, int], is_shared : bool) -> None:
	model_names = [ 'nsfw_1', 'nsfw_2', 'nsfw_3' ]
	_, model_source_set = content_analyser.collect_model_downloads()

	with patch('facefusion.inference_manager.has_execution_provider', return_value = True):
		with patch('facefusion.inference_manager.get_onnxruntime_version', return_value = onnxruntime_version):
			session_context.set_session_id('session-a')
			state_manager.init()
			init()
			session_a_inference_pool = get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

			session_context.set_session_id('session-b')
			state_manager.init()
			init()
			session_b_inference_pool = get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

	assert isinstance(session_a_inference_pool.get('nsfw_1'), InferenceSession)
	assert (session_a_inference_pool.get('nsfw_1') is session_b_inference_pool.get('nsfw_1')) == is_shared


def test_find_inference_pool() -> None:
	model_names = [ 'nsfw_1', 'nsfw_2', 'nsfw_3' ]
	_, model_source_set = content_analyser.collect_model_downloads()

	session_context.set_session_id('session-a')
	state_manager.init()
	init()
	inference_pool = get_inference_pool('facefusion.content_analyser', model_names, model_source_set)
	session_context.set_session_id('session-b')
	state_manager.init()
	init()

	assert find_inference_pool('facefusion.content_analyser.nsfw_1.nsfw_2.nsfw_3.0.cpu') is inference_pool
	assert find_inference_pool('invalid') is None


def test_create_inference_pool() -> None:
	_, model_source_set = content_analyser.collect_model_downloads()
	model_source_set['invalid'] =\
	{
		'url': 'invalid',
		'path': 'invalid'
	}
	inference_pool = create_inference_pool(model_source_set, [ 'CPUExecutionProvider' ])

	assert list(inference_pool.keys()) == [ 'nsfw_1', 'nsfw_2', 'nsfw_3' ]
	assert isinstance(inference_pool.get('nsfw_1'), InferenceSession)


def test_clear_inference_pool() -> None:
	model_names = [ 'nsfw_1', 'nsfw_2', 'nsfw_3' ]
	_, model_source_set = content_analyser.collect_model_downloads()

	session_context.set_session_id('session-a')
	state_manager.init()
	state_manager.set_item('execution_device_ids', [ 0, 1 ])
	init()
	get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

	assert list(store_creator.get_content(INFERENCE_POOL_STORE, 'session-a').keys()) == [ 'facefusion.content_analyser.nsfw_1.nsfw_2.nsfw_3.0.cpu', 'facefusion.content_analyser.nsfw_1.nsfw_2.nsfw_3.1.cpu' ]

	session_context.set_session_id('session-b')
	state_manager.init()
	state_manager.set_item('execution_device_ids', [ 0, 1 ])
	init()
	clear_inference_pool('facefusion.content_analyser', model_names)

	assert list(store_creator.get_content(INFERENCE_POOL_STORE, 'session-a').keys()) == [ 'facefusion.content_analyser.nsfw_1.nsfw_2.nsfw_3.0.cpu', 'facefusion.content_analyser.nsfw_1.nsfw_2.nsfw_3.1.cpu' ]

	session_context.set_session_id('session-a')
	clear_inference_pool('facefusion.content_analyser', [ 'nsfw_1' ])

	assert list(store_creator.get_content(INFERENCE_POOL_STORE, 'session-a').keys()) == [ 'facefusion.content_analyser.nsfw_1.nsfw_2.nsfw_3.0.cpu', 'facefusion.content_analyser.nsfw_1.nsfw_2.nsfw_3.1.cpu' ]

	clear_inference_pool('facefusion.content_analyser', model_names)

	assert store_creator.get_content(INFERENCE_POOL_STORE, 'session-a') == {}

	get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

	with patch('facefusion.inference_manager.is_windows', return_value = True):
		with patch('facefusion.inference_manager.has_execution_provider', return_value = True):
			clear_inference_pool('facefusion.content_analyser', [ 'invalid' ])

	assert store_creator.get_content(INFERENCE_POOL_STORE, 'session-a') == {}


def test_clear() -> None:
	model_names = [ 'nsfw_1', 'nsfw_2', 'nsfw_3' ]
	_, model_source_set = content_analyser.collect_model_downloads()

	session_context.set_session_id('session-a')
	state_manager.init()
	init()
	get_inference_pool('facefusion.content_analyser', model_names, model_source_set)
	clear()

	assert store_creator.get_content(INFERENCE_POOL_STORE, 'session-a') == {}

	session_manager.fork_session()
	state_manager.clone_state()
	get_inference_pool('facefusion.content_analyser', model_names, model_source_set)

	assert list(store_creator.get_content(INFERENCE_POOL_STORE, 'session-a').keys()) == [ 'facefusion.content_analyser.nsfw_1.nsfw_2.nsfw_3.0.cpu' ]

	clear()
	session_manager.join_session()

	assert store_creator.get_content(INFERENCE_POOL_STORE, 'session-a') == {}


def test_destroy() -> None:
	session_context.set_session_id('session-a')
	init()
	session_context.set_session_id('session-b')
	init()
	destroy('session-a')

	assert store_creator.has_content(INFERENCE_POOL_STORE, 'session-a') is False
	assert store_creator.has_content(INFERENCE_POOL_STORE, 'session-b') is True


def test_create_inference_session() -> None:
	_, model_source_set = content_analyser.collect_model_downloads()
	inference_session = create_inference_session(model_source_set.get('nsfw_1').get('path'), [ 'CPUExecutionProvider' ])

	assert isinstance(inference_session, InferenceSession)
	assert inference_session.get_providers() == [ 'CPUExecutionProvider' ]

	with patch('facefusion.inference_manager.fatal_exit') as exit_helper_mock:
		assert create_inference_session('invalid', [ 'CPUExecutionProvider' ]) is None

	assert exit_helper_mock.call_args.args == (1,)


def test_get_inference_context() -> None:
	assert get_inference_context('facefusion.content_analyser', [ 'nsfw_1', 'nsfw_2' ], 1, [ 'cuda', 'cpu' ]) == 'facefusion.content_analyser.nsfw_1.nsfw_2.1.cuda.cpu'


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
