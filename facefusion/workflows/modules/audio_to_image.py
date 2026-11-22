from functools import partial
from typing import Optional

from facefusion import state_manager
from facefusion.filesystem import get_file_extension, has_audio, has_image
from facefusion.types import ErrorCode, WorkflowMode
from facefusion.workflows.as_frames import create_temp_frames
from facefusion.workflows.core import clear, process_frames, setup
from facefusion.workflows.to_image import analyse_image
from facefusion.workflows.to_video import finalize_video, merge_frames, restore_audio


def detect() -> Optional[WorkflowMode]:
	target_path = state_manager.get_item('target_path')
	source_paths = state_manager.get_item('source_paths')
	output_path = state_manager.get_item('output_path')

	if get_file_extension(output_path) and has_image([ target_path ]) and has_audio(source_paths):
		return 'audio-to-image:video'

	return None


def process(start_time : float) -> ErrorCode:
	tasks =\
	[
		analyse_image,
		clear,
		setup,
		create_temp_frames,
		process_frames,
		merge_frames,
		restore_audio,
		partial(finalize_video, start_time),
		clear
	]

	for task in tasks:
		error_code = task() #type:ignore[operator]

		if error_code > 0:
			return error_code

	return 0
