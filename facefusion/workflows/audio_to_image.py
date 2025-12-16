from functools import partial

from facefusion import ffmpeg, logger, process_manager, state_manager, translator
from facefusion.audio import restrict_trim_audio_frame
from facefusion.common_helper import get_first
from facefusion.filesystem import filter_audio_paths
from facefusion.types import ErrorCode
from facefusion.vision import detect_image_resolution, restrict_image_resolution, scale_resolution
from facefusion.workflows.core import analyse_image, clear, is_process_stopping, process_frames, setup
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
