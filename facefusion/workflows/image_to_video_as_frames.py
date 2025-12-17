import os
from functools import partial

from facefusion import logger, process_manager, state_manager, translator
from facefusion.filesystem import are_images, copy_file, create_directory, resolve_file_paths
from facefusion.temp_helper import resolve_temp_frame_paths
from facefusion.time_helper import calculate_end_time
from facefusion.types import ErrorCode
from facefusion.workflows.core import clear, process_frames, setup
from facefusion.workflows.to_video import analyse_video, create_temp_frames


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

	process_manager.start()

	for task in tasks:
		error_code = task() #type:ignore[operator]

		if error_code > 0:
			process_manager.end()
			return error_code

	process_manager.end()
	return 0


def copy_temp_frames() -> ErrorCode:
	temp_frame_paths = resolve_temp_frame_paths(state_manager.get_temp_path(), state_manager.get_item('output_path'), state_manager.get_item('temp_frame_format'))

	for temp_frame_path in temp_frame_paths:
		if not create_directory(state_manager.get_item('output_path')) or not copy_file(temp_frame_path, os.path.join(state_manager.get_item('output_path'), os.path.basename(temp_frame_path))):
			return 1
	return 0


def finalize_frames(start_time : float) -> ErrorCode:
	if are_images(resolve_file_paths(state_manager.get_item('output_path'))):
		logger.info(translator.get('processing_frames_succeeded').format(seconds = calculate_end_time(start_time)), __name__)
	else:
		logger.error(translator.get('processing_frames_failed'), __name__)
		return 1
	return 0
