from functools import partial

from facefusion import process_manager
from facefusion.types import ErrorCode
from facefusion.workflows.as_frames import create_temp_frames
from facefusion.workflows.core import analyse_image, clear, process_frames, setup
from facefusion.workflows.to_video import finalize_video, merge_frames, restore_audio


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

	process_manager.start()

	for task in tasks:
		error_code = task() # type:ignore[operator]

		if error_code > 0:
			process_manager.end()
			return error_code

	process_manager.end()
	return 0
