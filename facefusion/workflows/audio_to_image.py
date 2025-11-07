import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

from tqdm import tqdm

from facefusion import ffmpeg, logger, process_manager, state_manager, translator
from facefusion.audio import count_audio_frame_total
from facefusion.common_helper import get_first
from facefusion.content_analyser import analyse_image
from facefusion.filesystem import filter_audio_paths, is_video, move_file
from facefusion.processors.core import get_processors_modules
from facefusion.temp_helper import clear_temp_directory, get_temp_file_path, get_temp_frame_sequence_paths
from facefusion.time_helper import calculate_end_time
from facefusion.types import ErrorCode
from facefusion.vision import detect_image_resolution, pack_resolution, restrict_image_resolution, scale_resolution
from facefusion.workflows.core import conditional_process_temp_frame, is_process_stopping, prepare_temp


def process(start_time : float) -> ErrorCode:
	tasks =\
	[
		setup,
		prepare_image,
		process_frames,
		merge_video,
		replace_audio,
		partial(finalize_video, start_time)
	]
	process_manager.start()

	for task in tasks:
		error_code = task() # type:ignore[operator]

		if error_code > 0:
			process_manager.end()
			return error_code

	process_manager.end()
	return 0


def setup() -> ErrorCode:
	if analyse_image(state_manager.get_item('target_path')):
		return 3

	prepare_temp()
	return 0


def prepare_image() -> ErrorCode:
	output_image_resolution = scale_resolution(detect_image_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_image_scale'))
	temp_image_resolution = restrict_image_resolution(state_manager.get_item('target_path'), output_image_resolution)

	logger.info(translator.get('copying_image').format(resolution = pack_resolution(temp_image_resolution)), __name__)
	if ffmpeg.copy_image(state_manager.get_item('target_path'), temp_image_resolution):
		logger.debug(translator.get('copying_image_succeeded'), __name__)
	else:
		logger.error(translator.get('copying_image_failed'), __name__)
		process_manager.end()
		return 1
	return 0


def process_frames() -> ErrorCode:
	source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
	audio_frame_total = count_audio_frame_total(source_audio_path, 25.0)
	output_video_fps = state_manager.get_item('output_video_fps')
	temp_frame_paths = get_temp_frame_sequence_paths(state_manager.get_item('target_path'), audio_frame_total, '%08d')

	if temp_frame_paths:
		with tqdm(total = len(temp_frame_paths), desc = translator.get('processing'), unit = 'frame', ascii = ' =', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
			progress.set_postfix(execution_providers = state_manager.get_item('execution_providers'))

			with ThreadPoolExecutor(max_workers = state_manager.get_item('execution_thread_count')) as executor:
				futures = []

				for frame_number, temp_frame_path in enumerate(temp_frame_paths):
					future = executor.submit(conditional_process_temp_frame, temp_frame_path, frame_number, output_video_fps)
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


def merge_video() -> ErrorCode:
	target_path = state_manager.get_item('target_path')
	output_video_fps = state_manager.get_item('output_video_fps')
	output_video_resolution = scale_resolution(detect_image_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_image_scale'))
	temp_video_fps = 25
	trim_frame_start, trim_frame_end = state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end')

	logger.info(translator.get('merging_video').format(resolution = pack_resolution(output_video_resolution), fps = output_video_fps), __name__)
	if ffmpeg.merge_video(target_path, temp_video_fps, output_video_resolution, output_video_fps, trim_frame_start, trim_frame_end):
		logger.debug(translator.get('merging_video_succeeded'), __name__)
	else:
		if is_process_stopping():
			return 4
		logger.error(translator.get('merging_video_failed'), __name__)
		return 1
	return 0


def replace_audio() -> ErrorCode:
	source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))

	if ffmpeg.replace_audio(state_manager.get_item('target_path'), source_audio_path, state_manager.get_item('output_path')):
		logger.debug(translator.get('replacing_audio_succeeded'), __name__)
	else:
		if is_process_stopping():
			return 4
		logger.warn(translator.get('replacing_audio_skipped'), __name__)
		temp_video_path = get_temp_file_path(state_manager.get_item('target_path'))
		temp_video_path = os.path.splitext(temp_video_path)[0] + '.mp4'
		move_file(temp_video_path, state_manager.get_item('output_path'))
	return 0


def finalize_video(start_time : float) -> ErrorCode:
	logger.debug(translator.get('clearing_temp'), __name__)
	clear_temp_directory(state_manager.get_item('target_path'))

	if is_video(state_manager.get_item('output_path')):
		logger.info(translator.get('processing_video_succeeded').format(seconds = calculate_end_time(start_time)), __name__)
	else:
		logger.error(translator.get('processing_video_failed'), __name__)
		return 1
	return 0
