from facefusion import content_analyser, ffmpeg, logger, state_manager, translator, video_manager
from facefusion.common_helper import get_first
from facefusion.filesystem import filter_audio_paths, is_video
from facefusion.media_helper import restrict_trim_frame
from facefusion.temp_helper import move_temp_file, resolve_temp_frame_paths
from facefusion.time_helper import calculate_end_time
from facefusion.types import ErrorCode, Fps, Resolution
from facefusion.vision import detect_image_resolution, detect_video_resolution, pack_resolution, restrict_trim_video_frame, restrict_video_fps, restrict_video_resolution, scale_resolution
from facefusion.workflows.core import is_process_stopping


def analyse_video() -> ErrorCode:
	trim_frame_start, trim_frame_end = restrict_trim_video_frame(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))

	if content_analyser.analyse_video(state_manager.get_item('target_path'), trim_frame_start, trim_frame_end):
		return 3
	return 0


def create_temp_frames() -> ErrorCode:
	trim_frame_start, trim_frame_end = restrict_trim_video_frame(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
	output_video_resolution = scale_resolution(detect_video_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_video_scale'))
	temp_video_resolution = restrict_video_resolution(state_manager.get_item('target_path'), output_video_resolution)
	temp_video_fps = restrict_video_fps(state_manager.get_item('target_path'), state_manager.get_item('output_video_fps'))
	logger.info(translator.get('extracting_frames').format(resolution=pack_resolution(temp_video_resolution), fps=temp_video_fps), __name__)

	if ffmpeg.extract_frames(state_manager.get_item('target_path'), state_manager.get_item('output_path'), temp_video_resolution, temp_video_fps, trim_frame_start, trim_frame_end):
		logger.debug(translator.get('extracting_frames_succeeded'), __name__)
	else:
		if is_process_stopping():
			return 4
		logger.error(translator.get('extracting_frames_failed'), __name__)
		return 1
	return 0


def merge_frames() -> ErrorCode:
	temp_frame_paths = resolve_temp_frame_paths(state_manager.get_temp_path(), state_manager.get_item('output_path'), state_manager.get_item('temp_frame_format'))
	trim_frame_start, trim_frame_end = restrict_trim_frame(len(temp_frame_paths), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
	output_video_resolution = conditional_scale_resolution()
	temp_video_fps = conditional_restrict_video_fps()

	logger.info(translator.get('merging_video').format(resolution = pack_resolution(output_video_resolution), fps = state_manager.get_item('output_video_fps')), __name__)
	if ffmpeg.merge_video(state_manager.get_item('target_path'), state_manager.get_item('output_path'), temp_video_fps, output_video_resolution, trim_frame_start, trim_frame_end):
		logger.debug(translator.get('merging_video_succeeded'), __name__)
	else:
		if is_process_stopping():
			return 4
		logger.error(translator.get('merging_video_failed'), __name__)
		return 1
	return 0


def restore_audio() -> ErrorCode:
	temp_frame_paths = resolve_temp_frame_paths(state_manager.get_temp_path(), state_manager.get_item('output_path'), state_manager.get_item('temp_frame_format'))
	trim_frame_start, trim_frame_end = restrict_trim_frame(len(temp_frame_paths), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))

	if state_manager.get_item('output_audio_volume') == 0:
		logger.info(translator.get('skipping_audio'), __name__)
		move_temp_file(state_manager.get_temp_path(), state_manager.get_item('output_path'))
	else:
		source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
		if source_audio_path:
			if ffmpeg.replace_audio(source_audio_path, state_manager.get_item('output_path')):
				conditional_clear_video_pool()
				logger.debug(translator.get('replacing_audio_succeeded'), __name__)
			else:
				conditional_clear_video_pool()
				if is_process_stopping():
					return 4
				logger.warn(translator.get('replacing_audio_skipped'), __name__)
				move_temp_file(state_manager.get_temp_path(), state_manager.get_item('output_path'))
		else:
			if ffmpeg.restore_audio(state_manager.get_item('target_path'), state_manager.get_item('output_path'), trim_frame_start, trim_frame_end):
				conditional_clear_video_pool()
				logger.debug(translator.get('restoring_audio_succeeded'), __name__)
			else:
				conditional_clear_video_pool()
				if is_process_stopping():
					return 4
				logger.warn(translator.get('restoring_audio_skipped'), __name__)
				move_temp_file(state_manager.get_temp_path(), state_manager.get_item('output_path'))
	return 0


def finalize_video(start_time : float) -> ErrorCode:
	if is_video(state_manager.get_item('output_path')):
		logger.info(translator.get('processing_video_succeeded').format(seconds = calculate_end_time(start_time)), __name__)
	else:
		logger.error(translator.get('processing_video_failed'), __name__)
		return 1
	return 0


def conditional_clear_video_pool() -> None:
	if state_manager.get_item('workflow') == 'image-to-video':
		video_manager.clear_video_pool()


def conditional_restrict_video_fps() -> Fps:
	if state_manager.get_item('workflow') == 'image-to-video':
		return restrict_video_fps(state_manager.get_item('target_path'), state_manager.get_item('output_video_fps'))
	return state_manager.get_item('output_video_fps')


def conditional_scale_resolution() -> Resolution:
	if state_manager.get_item('workflow') == 'image-to-video':
		return scale_resolution(detect_video_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_video_scale'))
	return scale_resolution(detect_image_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_video_scale'))
