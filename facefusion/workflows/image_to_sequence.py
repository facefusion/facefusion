import os
from functools import partial

from facefusion import content_analyser, logger, process_manager, state_manager, translator
from facefusion.filesystem import copy_file, create_directory, get_file_extension, get_file_format, get_file_name, is_sequence, resolve_file_pattern
from facefusion.temp_helper import get_temp_directory_path
from facefusion.time_helper import calculate_end_time
from facefusion.types import ErrorCode
from facefusion.vision import restrict_trim_frame
from facefusion.workflows.core import clear, conditional_get_output_path, conditional_resolve_temp_frame_paths, process_frames, setup


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
	target_paths = resolve_file_pattern(state_manager.get_item('target_pattern'))
	trim_frame_start, trim_frame_end = restrict_trim_frame(len(target_paths), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))

	if content_analyser.analyse_sequence(state_manager.get_item('target_pattern'), trim_frame_start, trim_frame_end):
		return 3
	return 0


def create_temp_frames() -> ErrorCode:
	target_paths = resolve_file_pattern(state_manager.get_item('target_pattern'))
	trim_frame_start, trim_frame_end = restrict_trim_frame(len(target_paths), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
	frame_range = range(trim_frame_start, trim_frame_end)
	temp_directory_path = get_temp_directory_path(state_manager.get_temp_path(), conditional_get_output_path())

	for frame_number in frame_range:
		if not copy_file(target_paths[frame_number], os.path.join(temp_directory_path, '{:08d}'.format(frame_number) + get_file_extension(target_paths[frame_number]))):
			return 1

	return 0


def move_frames() -> ErrorCode:
	target_paths = resolve_file_pattern(state_manager.get_item('target_pattern'))
	trim_frame_start, trim_frame_end = restrict_trim_frame(len(target_paths), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
	frame_range = range(trim_frame_start, trim_frame_end)
	temp_frame_paths = conditional_resolve_temp_frame_paths()
	create_directory(os.path.dirname(conditional_get_output_path()))

	for frame_number in frame_range:
		target_path = target_paths[frame_number]
		temp_frame_path = temp_frame_paths[frame_number % len(temp_frame_paths)]
		output_frame_path = state_manager.get_item('output_pattern').format(index = frame_number, target_name = get_file_name(target_path), target_extension = get_file_format(target_path))
		if not copy_file(temp_frame_path, output_frame_path):
			return 1
	return 0


def finalize_sequence(start_time : float) -> ErrorCode:
	if is_sequence(state_manager.get_item('output_pattern').format(index = '*', target_name = '*', target_extension = '*')):
		logger.info(translator.get('processing_sequence_succeeded').format(seconds = calculate_end_time(start_time)), __name__)
	else:
		logger.error(translator.get('processing_sequence_failed'), __name__)
		return 1
	return 0
