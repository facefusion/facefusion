import os
import sys
import importlib
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from types import ModuleType
from typing import Any, List, Callable
from tqdm import tqdm

import facefusion.globals
from facefusion import wording

FRAME_PROCESSORS_MODULES : List[ModuleType] = []
FRAME_PROCESSORS_METHODS =\
[
	'get_frame_processor',
	'clear_frame_processor',
	'pre_check',
	'pre_process',
	'process_frame',
	'process_frames',
	'process_image',
	'process_video',
	'post_process'
]


def load_frame_processor_module(frame_processor : str) -> Any:
	try:
		frame_processor_module = importlib.import_module('facefusion.processors.frame.modules.' + frame_processor)
		for method_name in FRAME_PROCESSORS_METHODS:
			if not hasattr(frame_processor_module, method_name):
				raise NotImplementedError
	except ModuleNotFoundError:
		sys.exit(wording.get('frame_processor_not_loaded').format(frame_processor = frame_processor))
	except NotImplementedError:
		sys.exit(wording.get('frame_processor_not_implemented').format(frame_processor = frame_processor))
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


def multi_process_frame(source_path : str, temp_frame_paths : List[str], process_frames: Callable[[str, List[str], Any], None], update: Callable[[], None]) -> None:
	with ThreadPoolExecutor(max_workers = facefusion.globals.execution_thread_count) as executor:
		futures = []
		queue = create_queue(temp_frame_paths)
		queue_per_future = max(len(temp_frame_paths) // facefusion.globals.execution_thread_count * facefusion.globals.execution_queue_count, 1)
		while not queue.empty():
			future = executor.submit(process_frames, source_path, pick_queue(queue, queue_per_future), update)
			futures.append(future)
		for future in as_completed(futures):
			future.result()


def create_queue(temp_frame_paths : List[str]) -> Queue[str]:
	queue: Queue[str] = Queue()
	for frame_path in temp_frame_paths:
		queue.put(frame_path)
	return queue


def pick_queue(queue : Queue[str], queue_per_future : int) -> List[str]:
	queues = []
	for _ in range(queue_per_future):
		if not queue.empty():
			queues.append(queue.get())
	return queues


def process_video(source_path : str, frame_paths : List[str], process_frames : Callable[[str, List[str], Any], None]) -> None:
	progress_bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
	total = len(frame_paths)
	with tqdm(total = total, desc = wording.get('processing'), unit = 'frame', dynamic_ncols = True, bar_format = progress_bar_format) as progress:
		multi_process_frame(source_path, frame_paths, process_frames, lambda: update_progress(progress))


def update_progress(progress : Any = None) -> None:
	process = psutil.Process(os.getpid())
	memory_usage = process.memory_info().rss / 1024 / 1024 / 1024
	progress.set_postfix(
	{
		'memory_usage': '{:.2f}'.format(memory_usage).zfill(5) + 'GB',
		'execution_providers': facefusion.globals.execution_providers,
		'execution_thread_count': facefusion.globals.execution_thread_count,
		'execution_queue_count': facefusion.globals.execution_queue_count
	})
	progress.refresh()
	progress.update(1)


def get_device() -> str:
	if 'CUDAExecutionProvider' in facefusion.globals.execution_providers:
		return 'cuda'
	if 'CoreMLExecutionProvider' in facefusion.globals.execution_providers:
		return 'mps'
	return 'cpu'
