from functools import partial
from typing import Optional

from facefusion import state_manager
from facefusion.filesystem import get_file_extension, has_video
from facefusion.types import ErrorCode, WorkflowMode
from facefusion.workflows.core import clear, process_frames, setup
from facefusion.workflows.to_video import analyse_video, create_temp_frames, finalize_video, merge_frames, process_memory_frames, restore_audio


def detect() -> Optional[WorkflowMode]:
	target_path = state_manager.get_item('target_path')
	output_path = state_manager.get_item('output_path')

	if get_file_extension(output_path) and has_video([ target_path ]):
		return 'image-to-video'

	return None


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
			create_temp_frames,
			process_frames,
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

	for task in tasks:
		error_code = task() #type:ignore[operator]

		if error_code > 0:
			return error_code

	return 0
