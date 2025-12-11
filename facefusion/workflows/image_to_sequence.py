import os
from functools import partial

from facefusion import content_analyser, logger, process_manager, state_manager, translator
from facefusion.filesystem import copy_file, create_directory, is_sequence, resolve_file_pattern
from facefusion.temp_helper import get_temp_directory_path
from facefusion.temp_helper import resolve_temp_frame_paths
from facefusion.time_helper import calculate_end_time
from facefusion.types import ErrorCode
from facefusion.vision import restrict_trim_frame
from facefusion.workflows.core import clear, process_frames, setup


def process(start_time : float) -> ErrorCode:
	tasks =\
	[
		analyse_sequence,
		clear,
		setup,
		create_temp_frames,
		process_frames,
		move_frames,
		partial(finalize_sequence, start_time),
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


def analyse_sequence() -> ErrorCode:
	sequence_frame_paths = resolve_file_pattern(state_manager.get_item('target_path'))
	trim_frame_start, trim_frame_end = restrict_trim_frame(len(sequence_frame_paths), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))

	if content_analyser.analyse_sequence(state_manager.get_item('target_path'), trim_frame_start, trim_frame_end):
		return 3
	return 0


def create_temp_frames() -> ErrorCode:
	sequence_frame_paths = resolve_file_pattern(state_manager.get_item('target_path'))
	trim_frame_start, trim_frame_end = restrict_trim_frame(len(sequence_frame_paths), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
	temp_directory_path = get_temp_directory_path(state_manager.get_temp_path(), state_manager.get_item('output_path'))

	for index in range(trim_frame_start, trim_frame_end): # TODO create dedicated method
		if not copy_file(sequence_frame_paths[index], os.path.join(temp_directory_path, '{:08d}'.format(index) + '.' + state_manager.get_item('temp_frame_format'))):
			return 1

	return 0


def move_frames() -> ErrorCode:
	temp_frame_paths = resolve_temp_frame_paths(state_manager.get_temp_path(), state_manager.get_item('output_path'), state_manager.get_item('temp_frame_format'))
	create_directory(os.path.dirname(state_manager.get_item('output_path')))

	for index, temp_frame_path in enumerate(temp_frame_paths): # TODO use trim naming
		if not copy_file(temp_frame_path, state_manager.get_item('output_path') % index):
			return 1
	return 0


def finalize_sequence(start_time : float) -> ErrorCode:
	if is_sequence(state_manager.get_item('output_path')):
		logger.info(translator.get('processing_sequence_succeeded').format(seconds = calculate_end_time(start_time)), __name__)
	else:
		logger.error(translator.get('processing_sequence_failed'), __name__)
		return 1
	return 0
