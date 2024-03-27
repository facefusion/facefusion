import os
import sys
import importlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from types import ModuleType
from typing import Any, List
from tqdm import tqdm

import facefusion.globals
from facefusion.typing import ProcessFrames, QueuePayload
from facefusion.execution import encode_execution_providers
from facefusion import logger, wording

FRAME_PROCESSORS_MODULES : List[ModuleType] = []
FRAME_PROCESSORS_METHODS =\
[
	'get_frame_processor',
	'clear_frame_processor',
	'get_options',
	'set_options',
	'register_args',
	'apply_args',
	'pre_check',
	'post_check',
	'pre_process',
	'post_process',
	'get_reference_frame',
	'process_frame',
	'process_frames',
	'process_image',
	'process_video'
]


def load_frame_processor_module(frame_processor : str) -> Any:
	try:
		frame_processor_module = importlib.import_module('facefusion.processors.frame.modules.' + frame_processor)
		for method_name in FRAME_PROCESSORS_METHODS:
			if not hasattr(frame_processor_module, method_name):
				raise NotImplementedError
	except ModuleNotFoundError as exception:
		logger.error(wording.get('frame_processor_not_loaded').format(frame_processor = frame_processor), __name__.upper())
		logger.debug(exception.msg, __name__.upper())
		sys.exit(1)
	except NotImplementedError:
		logger.error(wording.get('frame_processor_not_implemented').format(frame_processor = frame_processor), __name__.upper())
		sys.exit(1)
	return frame_processor_module


def get_frame_processors_modules(frame_processors : List[str]) -> List[ModuleType]:
	global FRAME_PROCESSORS_MODULES

	if not FRAME_PROCESSORS_MODULES:
		for frame_processor in frame_processors:
			frame_processor_module = load_frame_processor_module(frame_processor)
			FRAME_PROCESSORS_MODULES.append(frame_processor_module)
	return FRAME_PROCESSORS_MODULES


def clear_frame_processors_modules() -> None:
	global FRAME_PROCESSORS_MODULES

	for frame_processor_module in get_frame_processors_modules(facefusion.globals.frame_processors):
		frame_processor_module.clear_frame_processor()
	FRAME_PROCESSORS_MODULES = []


def multi_process_frames(source_paths : List[str], temp_frame_paths : List[str], process_frames : ProcessFrames) -> None:
	queue_payloads = create_queue_payloads(temp_frame_paths)
	with tqdm(total = len(queue_payloads), desc = wording.get('processing'), unit = 'frame', ascii = ' =', disable = facefusion.globals.log_level in [ 'warn', 'error' ]) as progress:
		progress.set_postfix(
		{
			'execution_providers': encode_execution_providers(facefusion.globals.execution_providers),
			'execution_thread_count': facefusion.globals.execution_thread_count,
			'execution_queue_count': facefusion.globals.execution_queue_count
		})
		with ThreadPoolExecutor(max_workers = facefusion.globals.execution_thread_count) as executor:
			futures = []
			queue : Queue[QueuePayload] = create_queue(queue_payloads)
			queue_per_future = max(len(queue_payloads) // facefusion.globals.execution_thread_count * facefusion.globals.execution_queue_count, 1)
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
