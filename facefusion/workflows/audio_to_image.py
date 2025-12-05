from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

from tqdm import tqdm

from facefusion import content_analyser, ffmpeg, logger, process_manager, state_manager, translator
from facefusion.audio import restrict_trim_audio_frame
from facefusion.common_helper import get_first
from facefusion.filesystem import filter_audio_paths, is_video
from facefusion.processors.core import get_processors_modules
from facefusion.temp_helper import move_temp_file, resolve_temp_frame_paths
from facefusion.time_helper import calculate_end_time
from facefusion.types import ErrorCode
from facefusion.vision import detect_image_resolution, pack_resolution, restrict_image_resolution, restrict_trim_video_frame, scale_resolution
from facefusion.workflows.core import clear, is_process_stopping, process_temp_frame, setup


def process(start_time : float) -> ErrorCode:
	tasks =\
	[
		analyse_image,
		clear,
		setup,
		create_temp_frames,
		process_image,
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


def analyse_image() -> ErrorCode: # TODO: reusable block
	if content_analyser.analyse_image(state_manager.get_item('target_path')):
		return 3
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


def process_image() -> ErrorCode:
	temp_frame_paths = resolve_temp_frame_paths(state_manager.get_temp_path(), state_manager.get_item('output_path'), state_manager.get_item('temp_frame_format'))

	if temp_frame_paths:
		with tqdm(total = len(temp_frame_paths), desc = translator.get('processing'), unit = 'frame', ascii = ' =', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
			progress.set_postfix(execution_providers = state_manager.get_item('execution_providers'))

			with ThreadPoolExecutor(max_workers = state_manager.get_item('execution_thread_count')) as executor:
				futures = []

				for frame_number, temp_frame_path in enumerate(temp_frame_paths):
					future = executor.submit(process_temp_frame, temp_frame_path, frame_number)
					futures.append(future)

				for future in as_completed(futures):
					if is_process_stopping():
						for __future__ in futures:
							__future__.cancel()

					if not future.cancelled():
						future.result()
						progress.update()

		for processor_module in get_processors_modules(state_manager.get_item('processors')):
			processor_module.post_process()

		if is_process_stopping():
			return 4
	else:
		logger.error(translator.get('temp_frames_not_found'), __name__)
		return 1
	return 0


def merge_frames() -> ErrorCode:
	trim_frame_start, trim_frame_end = restrict_trim_video_frame(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
	output_video_resolution = scale_resolution(detect_image_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_image_scale'))

	logger.info(translator.get('merging_video').format(resolution = pack_resolution(output_video_resolution), fps = state_manager.get_item('output_video_fps')), __name__)
	if ffmpeg.merge_video(state_manager.get_item('target_path'), state_manager.get_item('output_path'), state_manager.get_item('output_video_fps'), output_video_resolution, trim_frame_start, trim_frame_end):
		logger.debug(translator.get('merging_video_succeeded'), __name__)
	else:
		if is_process_stopping():
			return 4
		logger.error(translator.get('merging_video_failed'), __name__)
		return 1
	return 0


def restore_audio() -> ErrorCode:
	if state_manager.get_item('output_audio_volume') == 0:
		logger.info(translator.get('skipping_audio'), __name__)
		move_temp_file(state_manager.get_temp_path(), state_manager.get_item('output_path'))
	else:
		source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
		if source_audio_path:
			if ffmpeg.replace_audio(source_audio_path, state_manager.get_item('output_path')):
				logger.debug(translator.get('replacing_audio_succeeded'), __name__)
			else:
				if is_process_stopping():
					return 4
				logger.warn(translator.get('replacing_audio_skipped'), __name__)
				move_temp_file(state_manager.get_temp_path(), state_manager.get_item('output_path'))
	return 0


def finalize_video(start_time : float) -> ErrorCode:
	if is_video(state_manager.get_item('output_path')):
		logger.info(translator.get('processing_video_succeeded').format(seconds = calculate_end_time(start_time)), __name__)
	else:
		logger.error(translator.get('processing_video_failed'), __name__)
		return 1
	return 0
