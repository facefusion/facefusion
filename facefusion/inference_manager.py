from time import sleep

from facefusion import process_manager, state_manager
from facefusion.execution import create_inference_pool
from facefusion.thread_helper import thread_lock
from facefusion.typing import DownloadSet, InferencePool, InferencePoolSet

INFERENCE_POOLS : InferencePoolSet = {}


def get_inference_pool(model_context : str, model_sources : DownloadSet) -> InferencePool:
	global INFERENCE_POOLS

	with thread_lock():
		while process_manager.is_checking():
			sleep(0.5)
		if INFERENCE_POOLS.get(model_context) is None:
			INFERENCE_POOLS[model_context] = create_inference_pool(model_sources, state_manager.get_item('execution_device_id'), state_manager.get_item('execution_providers'))
		return INFERENCE_POOLS.get(model_context)


def clear_inference_pool(model_context : str) -> None:
	global INFERENCE_POOLS

	INFERENCE_POOLS[model_context] = None
