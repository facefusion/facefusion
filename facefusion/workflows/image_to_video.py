from functools import partial

from facefusion import process_manager, state_manager
from facefusion.types import ErrorCode
from facefusion.workflows.core import clear, setup
from facefusion.workflows.to_video import analyse_video, extract_frames, finalize_video, merge_frames, process_disk_frames, process_memory_frames, restore_audio


def process(start_time : float) -> ErrorCode:
	tasks =\
	[
		analyse_video,
		clear,
		setup
	]

	if state_manager.get_item('workflow_strategy') == 'disk':
		tasks.extend(
		[
			extract_frames,
			process_disk_frames,
			merge_frames
		])

	if state_manager.get_item('workflow_strategy') == 'memory':
		tasks.append(process_memory_frames)

	tasks.extend(
	[
		restore_audio,
		partial(finalize_video, start_time),
		clear
	])
	process_manager.start()

	for task in tasks:
		error_code = task() #type:ignore[operator]

		if error_code > 0:
			process_manager.end()
			return error_code

	process_manager.end()
	return 0
