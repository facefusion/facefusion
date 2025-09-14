import importlib
import random
from time import sleep, time
from typing import List, Optional

from onnxruntime import InferenceSession, SessionOptions, GraphOptimizationLevel, ExecutionMode

from facefusion import logger, process_manager, state_manager, wording
from facefusion.app_context import detect_app_context
from facefusion.execution import create_inference_session_providers
from facefusion.exit_helper import fatal_exit
from facefusion.filesystem import get_file_name, is_file
from facefusion.time_helper import calculate_end_time
from facefusion.types import DownloadSet, ExecutionProvider, InferencePool, InferencePoolSet

INFERENCE_POOL_SET : InferencePoolSet =\
{
	'cli': {},
	'ui': {}
}


def get_inference_pool(module_name : str, model_names : List[str], model_source_set : DownloadSet) -> InferencePool:
	while process_manager.is_checking():
		sleep(0.5)
	execution_device_ids = state_manager.get_item('execution_device_ids')
	execution_providers = resolve_execution_providers(module_name)
	app_context = detect_app_context()

	for execution_device_id in execution_device_ids:
		inference_context = get_inference_context(module_name, model_names, execution_device_id, execution_providers)

		if app_context == 'cli' and INFERENCE_POOL_SET.get('ui').get(inference_context):
			INFERENCE_POOL_SET['cli'][inference_context] = INFERENCE_POOL_SET.get('ui').get(inference_context)
		if app_context == 'ui' and INFERENCE_POOL_SET.get('cli').get(inference_context):
			INFERENCE_POOL_SET['ui'][inference_context] = INFERENCE_POOL_SET.get('cli').get(inference_context)
		if not INFERENCE_POOL_SET.get(app_context).get(inference_context):
			INFERENCE_POOL_SET[app_context][inference_context] = create_inference_pool(model_source_set, execution_device_id, execution_providers)

	current_inference_context = get_inference_context(module_name, model_names, random.choice(execution_device_ids), execution_providers)
	return INFERENCE_POOL_SET.get(app_context).get(current_inference_context)


def create_inference_pool(model_source_set : DownloadSet, execution_device_id : str, execution_providers : List[ExecutionProvider]) -> InferencePool:
	inference_pool : InferencePool = {}

	for model_name in model_source_set.keys():
		model_path = model_source_set.get(model_name).get('path')
		if is_file(model_path):
			inference_pool[model_name] = create_inference_session(model_path, execution_device_id, execution_providers)

	return inference_pool


def clear_inference_pool(module_name : str, model_names : List[str]) -> None:
	execution_device_ids = state_manager.get_item('execution_device_ids')
	execution_providers = resolve_execution_providers(module_name)
	app_context = detect_app_context()

	for execution_device_id in execution_device_ids:
		inference_context = get_inference_context(module_name, model_names, execution_device_id, execution_providers)

		if INFERENCE_POOL_SET.get(app_context).get(inference_context):
			del INFERENCE_POOL_SET[app_context][inference_context]


def create_inference_session(model_path : str, execution_device_id : str, execution_providers : List[ExecutionProvider]) -> InferenceSession:
    model_file_name = get_file_name(model_path)
    start_time = time()

    inference_session: Optional[InferenceSession] = None
    try:
        inference_session_providers = create_inference_session_providers(execution_device_id, execution_providers)
        sess_options = SessionOptions()
        # Maximize graph optimizations
        sess_options.graph_optimization_level = GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.enable_mem_pattern = True
        # Adaptive threading: keep CPU/CoreML parallel, constrain for CUDA/TRT
        lower_providers = [p.lower() for p in execution_providers]
        uses_gpu = any(p in ('cuda', 'tensorrt') for p in lower_providers)
        if uses_gpu:
            # GPU-bound: avoid CPU contention
            sess_options.intra_op_num_threads = 1
            sess_options.inter_op_num_threads = 1
        else:
            # Let ORT parallelize on CPU; keep defaults or set PARALLEL mode
            try:
                sess_options.execution_mode = ExecutionMode.ORT_PARALLEL
            except Exception:
                pass
        inference_session = InferenceSession(model_path, sess_options = sess_options, providers = inference_session_providers)
    except Exception as exception:
        logger.error(wording.get('loading_model_failed').format(model_name = model_file_name), __name__)
        logger.debug(str(exception), __name__)
        fatal_exit(1)

    assert inference_session is not None
    logger.debug(wording.get('loading_model_succeeded').format(model_name = model_file_name, seconds = calculate_end_time(start_time)), __name__)
    return inference_session


def get_inference_context(module_name : str, model_names : List[str], execution_device_id : str, execution_providers : List[ExecutionProvider]) -> str:
	inference_context = '.'.join([ module_name ] + model_names + [ execution_device_id ] + list(execution_providers))
	return inference_context


def resolve_execution_providers(module_name : str) -> List[ExecutionProvider]:
	module = importlib.import_module(module_name)

	if hasattr(module, 'resolve_execution_providers'):
		return getattr(module, 'resolve_execution_providers')()
	return state_manager.get_item('execution_providers')
