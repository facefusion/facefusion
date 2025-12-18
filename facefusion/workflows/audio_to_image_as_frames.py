import os
from functools import partial

from facefusion import ffmpeg, logger, process_manager, state_manager, translator
from facefusion.audio import restrict_trim_audio_frame
from facefusion.common_helper import get_first
from facefusion.filesystem import are_images, resolve_file_paths
from facefusion.filesystem import copy_file, create_directory, filter_audio_paths
from facefusion.temp_helper import resolve_temp_frame_paths
from facefusion.time_helper import calculate_end_time
from facefusion.types import ErrorCode
from facefusion.vision import detect_image_resolution, restrict_image_resolution, scale_resolution
from facefusion.workflows.core import analyse_image, clear, is_process_stopping, process_frames, setup


def process(start_time : float) -> ErrorCode:
	tasks =\
	[
		analyse_image,
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


def create_temp_frames() -> ErrorCode:
	state_manager.set_item('output_video_fps', 25.0)  # TODO: set default fps value
	source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
	output_image_resolution = scale_resolution(detect_image_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_image_scale'))
	temp_image_resolution = restrict_image_resolution(state_manager.get_item('target_path'), output_image_resolution)
	trim_frame_start, trim_frame_end = restrict_trim_audio_frame(source_audio_path, state_manager.get_item('output_video_fps'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))

	if ffmpeg.spawn_frames(state_manager.get_item('target_path'), state_manager.get_item('output_path'), temp_image_resolution, state_manager.get_item('output_video_fps'), trim_frame_start, trim_frame_end):
		logger.debug(translator.get('spawning_frames_succeeded'), __name__)
	else:
		if is_process_stopping():
			return 4
		logger.error(translator.get('spawning_frames_failed'), __name__)
		return 1
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
