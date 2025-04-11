import importlib
from time import sleep
from typing import List

from onnxruntime import InferenceSession

from facefusion import process_manager, state_manager
from facefusion.app_context import detect_app_context
from facefusion.execution import create_inference_session_providers
from facefusion.filesystem import is_file
from facefusion.types import DownloadSet, ExecutionProvider, InferencePool, InferencePoolSet

INFERENCE_POOL_SET : InferencePoolSet =\
{
	'cli': {},
	'ui': {}
}


def get_inference_pool(module_name : str, model_names : List[str], model_source_set : DownloadSet) -> InferencePool:
	while process_manager.is_checking():
		sleep(0.5)
	execution_device_id = state_manager.get_item('execution_device_id')
	execution_providers = resolve_execution_providers(module_name)
	app_context = detect_app_context()
	inference_context = get_inference_context(module_name, model_names, execution_device_id, execution_providers)

	if app_context == 'cli' and INFERENCE_POOL_SET.get('ui').get(inference_context):
		INFERENCE_POOL_SET['cli'][inference_context] = INFERENCE_POOL_SET.get('ui').get(inference_context)
	if app_context == 'ui' and INFERENCE_POOL_SET.get('cli').get(inference_context):
		INFERENCE_POOL_SET['ui'][inference_context] = INFERENCE_POOL_SET.get('cli').get(inference_context)
	if not INFERENCE_POOL_SET.get(app_context).get(inference_context):
		INFERENCE_POOL_SET[app_context][inference_context] = create_inference_pool(model_source_set, execution_device_id, execution_providers)

	return INFERENCE_POOL_SET.get(app_context).get(inference_context)


def create_inference_pool(model_source_set : DownloadSet, execution_device_id : str, execution_providers : List[ExecutionProvider]) -> InferencePool:
	inference_pool : InferencePool = {}

	for model_name in model_source_set.keys():
		model_path = model_source_set.get(model_name).get('path')
		if is_file(model_path):
			inference_pool[model_name] = create_inference_session(model_path, execution_device_id, execution_providers)

	return inference_pool


def clear_inference_pool(module_name : str, model_names : List[str]) -> None:
	execution_device_id = state_manager.get_item('execution_device_id')
	execution_providers = resolve_execution_providers(module_name)
	app_context = detect_app_context()
	inference_context = get_inference_context(module_name, model_names, execution_device_id, execution_providers)

	if INFERENCE_POOL_SET.get(app_context).get(inference_context):
		del INFERENCE_POOL_SET[app_context][inference_context]


def create_inference_session(model_path : str, execution_device_id : str, execution_providers : List[ExecutionProvider]) -> InferenceSession:
	inference_session_providers = create_inference_session_providers(execution_device_id, execution_providers)
	return InferenceSession(model_path, providers = inference_session_providers)


def get_inference_context(module_name : str, model_names : List[str], execution_device_id : str, execution_providers : List[ExecutionProvider]) -> str:
	inference_context = '.'.join([ module_name ] + model_names + [ execution_device_id ] + list(execution_providers))
	return inference_context


def resolve_execution_providers(module_name : str) -> List[ExecutionProvider]:
	module = importlib.import_module(module_name)

	if hasattr(module, 'resolve_execution_providers'):
		return getattr(module, 'resolve_execution_providers')()
	return state_manager.get_item('execution_providers')
