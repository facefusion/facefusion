from functools import partial
from typing import Optional

from facefusion import state_manager
from facefusion.filesystem import get_file_extension, has_video
from facefusion.types import ErrorCode, WorkflowMode
from facefusion.workflows.as_frames import copy_temp_frames, finalize_frames
from facefusion.workflows.core import clear, process_frames, setup
from facefusion.workflows.to_video import analyse_video, create_temp_frames


def detect() -> Optional[WorkflowMode]:
	target_path = state_manager.get_item('target_path')
	output_path = state_manager.get_item('output_path')

	if get_file_extension(output_path) is None and has_video([ target_path ]):
		return 'image-to-video:frames'

	return None


def process(start_time : float) -> ErrorCode:
	tasks =\
	[
		analyse_video,
		clear,
		setup,
		create_temp_frames,
		process_frames,
		copy_temp_frames,
		partial(finalize_frames, start_time),
		clear
	]

	for task in tasks:
		error_code = task() #type:ignore[operator]

		if error_code > 0:
			return error_code

	return 0
