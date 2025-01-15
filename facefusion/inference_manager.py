from time import sleep
from typing import List

from onnxruntime import InferenceSession

from facefusion import process_manager, state_manager
from facefusion.app_context import detect_app_context
from facefusion.execution import create_inference_execution_providers, has_execution_provider
from facefusion.filesystem import is_file
from facefusion.typing import DownloadSet, ExecutionProvider, InferencePool, InferencePoolSet

INFERENCE_POOLS : InferencePoolSet =\
{
	'cli': {}, #type:ignore[typeddict-item]
	'ui': {} #type:ignore[typeddict-item]
}


def get_inference_pool(model_context : str, model_sources : DownloadSet) -> InferencePool:
	global INFERENCE_POOLS

	while process_manager.is_checking():
		sleep(0.5)
	app_context = detect_app_context()
	inference_context = get_inference_context(model_context)

	if app_context == 'cli' and INFERENCE_POOLS.get('ui').get(inference_context):
		INFERENCE_POOLS['cli'][inference_context] = INFERENCE_POOLS.get('ui').get(inference_context)
	if app_context == 'ui' and INFERENCE_POOLS.get('cli').get(inference_context):
		INFERENCE_POOLS['ui'][inference_context] = INFERENCE_POOLS.get('cli').get(inference_context)
	if not INFERENCE_POOLS.get(app_context).get(inference_context):
		INFERENCE_POOLS[app_context][inference_context] = create_inference_pool(model_sources, state_manager.get_item('execution_device_id'), resolve_execution_providers(model_context))

	return INFERENCE_POOLS.get(app_context).get(inference_context)


def create_inference_pool(model_sources : DownloadSet, execution_device_id : str, execution_providers : List[ExecutionProvider]) -> InferencePool:
	inference_pool : InferencePool = {}

	for model_name in model_sources.keys():
		model_path = model_sources.get(model_name).get('path')
		if is_file(model_path):
			inference_pool[model_name] = create_inference_session(model_path, execution_device_id, execution_providers)

	return inference_pool


def clear_inference_pool(model_context : str) -> None:
	global INFERENCE_POOLS

	app_context = detect_app_context()
	inference_context = get_inference_context(model_context)

	if INFERENCE_POOLS.get(app_context).get(inference_context):
		del INFERENCE_POOLS[app_context][inference_context]


def create_inference_session(model_path : str, execution_device_id : str, execution_providers : List[ExecutionProvider]) -> InferenceSession:
	inference_execution_providers = create_inference_execution_providers(execution_device_id, execution_providers)
	return InferenceSession(model_path, providers = inference_execution_providers)


def get_inference_context(model_context : str) -> str:
	inference_context = model_context + '.' + '_'.join(state_manager.get_item('execution_providers'))
	return inference_context


def resolve_execution_providers(model_context : str) -> List[ExecutionProvider]:
	if has_execution_provider('coreml') and model_context == 'facefusion.processors.modules.frame_colorizer':
		return [ 'cpu' ]
	return state_manager.get_item('execution_providers')
