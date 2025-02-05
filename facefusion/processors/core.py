import importlib
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from types import ModuleType
from typing import Any, List

from tqdm import tqdm

from facefusion import logger, state_manager, wording
from facefusion.exit_helper import hard_exit
from facefusion.types import ProcessFrames, QueuePayload

PROCESSORS_METHODS =\
[
	'get_inference_pool',
	'clear_inference_pool',
	'register_args',
	'apply_args',
	'pre_check',
	'pre_process',
	'post_process',
	'get_reference_frame',
	'process_frame',
	'process_frames',
	'process_image',
	'process_video'
]


def load_processor_module(processor : str) -> Any:
	try:
		processor_module = importlib.import_module('facefusion.processors.modules.' + processor)
		for method_name in PROCESSORS_METHODS:
			if not hasattr(processor_module, method_name):
				raise NotImplementedError
	except ModuleNotFoundError as exception:
		logger.error(wording.get('processor_not_loaded').format(processor = processor), __name__)
		logger.debug(exception.msg, __name__)
		hard_exit(1)
	except NotImplementedError:
		logger.error(wording.get('processor_not_implemented').format(processor = processor), __name__)
		hard_exit(1)
	return processor_module


def get_processors_modules(processors : List[str]) -> List[ModuleType]:
	processor_modules = []

	for processor in processors:
		processor_module = load_processor_module(processor)
		processor_modules.append(processor_module)
	return processor_modules


def multi_process_frames(source_paths : List[str], temp_frame_paths : List[str], process_frames : ProcessFrames) -> None:
	queue_payloads = create_queue_payloads(temp_frame_paths)
	with tqdm(total = len(queue_payloads), desc = wording.get('processing'), unit = 'frame', ascii = ' =', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
		progress.set_postfix(execution_providers = state_manager.get_item('execution_providers'))
		with ThreadPoolExecutor(max_workers = state_manager.get_item('execution_thread_count')) as executor:
			futures = []
			queue : Queue[QueuePayload] = create_queue(queue_payloads)
			queue_per_future = max(len(queue_payloads) // state_manager.get_item('execution_thread_count') * state_manager.get_item('execution_queue_count'), 1)

			while not queue.empty():
				future = executor.submit(process_frames, source_paths, pick_queue(queue, queue_per_future), progress.update)
				futures.append(future)

			for future_done in as_completed(futures):
				future_done.result()


def create_queue(queue_payloads : List[QueuePayload]) -> Queue[QueuePayload]:
	queue : Queue[QueuePayload] = Queue()
	for queue_payload in queue_payloads:
		queue.put(queue_payload)
	return queue


def pick_queue(queue : Queue[QueuePayload], queue_per_future : int) -> List[QueuePayload]:
	queues = []
	for _ in range(queue_per_future):
		if not queue.empty():
			queues.append(queue.get())
	return queues


def create_queue_payloads(temp_frame_paths : List[str]) -> List[QueuePayload]:
	queue_payloads = []
	temp_frame_paths = sorted(temp_frame_paths, key = os.path.basename)

	for frame_number, frame_path in enumerate(temp_frame_paths):
		frame_payload : QueuePayload =\
		{
			'frame_number': frame_number,
			'frame_path': frame_path
		}
		queue_payloads.append(frame_payload)
	return queue_payloads
