import importlib
import random
from functools import lru_cache
from time import sleep, time
from typing import List

from onnxruntime import InferenceSession

from facefusion import logger, process_manager, state_manager, translator
from facefusion.app_context import detect_app_context
from facefusion.common_helper import is_windows
from facefusion.execution import create_inference_providers, has_execution_provider
from facefusion.exit_helper import fatal_exit
from facefusion.filesystem import get_file_name, is_file
from facefusion.time_helper import calculate_end_time
from facefusion.types import DownloadSet, ExecutionProvider, InferencePool, InferencePoolSet, InferenceProvider

INFERENCE_POOL_SET : InferencePoolSet =\
{
	'cli': {},
	'ui': {}
}


def get_inference_pool(module_name : str, model_names : List[str], model_source_set : DownloadSet) -> InferencePool:
	while process_manager.is_checking():
		sleep(0.5)
	execution_device_ids = state_manager.get_item('execution_device_ids')
	execution_providers = state_manager.get_item('execution_providers')
	app_context = detect_app_context()

	for execution_device_id in execution_device_ids:
		inference_context = get_inference_context(module_name, model_names, execution_device_id, execution_providers)

		if app_context == 'cli' and INFERENCE_POOL_SET.get('ui').get(inference_context):
			INFERENCE_POOL_SET['cli'][inference_context] = INFERENCE_POOL_SET.get('ui').get(inference_context)
		if app_context == 'ui' and INFERENCE_POOL_SET.get('cli').get(inference_context):
			INFERENCE_POOL_SET['ui'][inference_context] = INFERENCE_POOL_SET.get('cli').get(inference_context)
		if not INFERENCE_POOL_SET.get(app_context).get(inference_context):
			inference_providers = resolve_static_inference_providers(module_name, execution_device_id)
			INFERENCE_POOL_SET[app_context][inference_context] = create_inference_pool(model_source_set, inference_providers)

	current_inference_context = get_inference_context(module_name, model_names, random.choice(execution_device_ids), execution_providers)
	return INFERENCE_POOL_SET.get(app_context).get(current_inference_context)


def create_inference_pool(model_source_set : DownloadSet, inference_providers : List[InferenceProvider]) -> InferencePool:
	inference_pool : InferencePool = {}

	for model_name in model_source_set.keys():
		model_path = model_source_set.get(model_name).get('path')
		if is_file(model_path):
			inference_pool[model_name] = create_inference_session(model_path, inference_providers)

	return inference_pool


def clear_inference_pool(module_name : str, model_names : List[str]) -> None:
	execution_device_ids = state_manager.get_item('execution_device_ids')
	execution_providers = state_manager.get_item('execution_providers')
	app_context = detect_app_context()

	if is_windows() and has_execution_provider('directml'):
		INFERENCE_POOL_SET[app_context].clear()

	for execution_device_id in execution_device_ids:
		inference_context = get_inference_context(module_name, model_names, execution_device_id, execution_providers)
		if INFERENCE_POOL_SET.get(app_context).get(inference_context):
			del INFERENCE_POOL_SET[app_context][inference_context]


def create_inference_session(model_path : str, inference_providers : List[InferenceProvider]) -> InferenceSession:
	model_file_name = get_file_name(model_path)
	start_time = time()

	try:
		inference_session = InferenceSession(model_path, providers = inference_providers)
		logger.debug(translator.get('loading_model_succeeded').format(model_name = model_file_name, seconds = calculate_end_time(start_time)), __name__)
		return inference_session

	except Exception:
		logger.error(translator.get('loading_model_failed').format(model_name = model_file_name), __name__)
		fatal_exit(1)


def get_inference_context(module_name : str, model_names : List[str], execution_device_id : int, execution_providers : List[ExecutionProvider]) -> str:
	inference_context = '.'.join([ module_name ] + model_names + [ str(execution_device_id) ] + list(execution_providers))
	return inference_context


@lru_cache()
def resolve_static_inference_providers(module_name : str, execution_device_id : int) -> List[InferenceProvider]:
	module = importlib.import_module(module_name)
	execution_providers = state_manager.get_item('execution_providers')

	if hasattr(module, 'resolve_inference_providers'):
		inference_providers = getattr(module, 'resolve_inference_providers')()

		if inference_providers:
			return inference_providers

	return create_inference_providers(execution_device_id, execution_providers)
