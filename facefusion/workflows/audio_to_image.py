from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

import numpy
from tqdm import tqdm

from facefusion import content_analyser, ffmpeg, logger, process_manager, state_manager, translator
from facefusion.audio import create_empty_audio_frame, get_audio_frame, get_voice_frame, restrict_trim_audio_frame
from facefusion.common_helper import get_first
from facefusion.filesystem import filter_audio_paths, is_video
from facefusion.processors.core import get_processors_modules
from facefusion.temp_helper import get_temp_sequence_paths, move_temp_file
from facefusion.time_helper import calculate_end_time
from facefusion.types import ErrorCode
from facefusion.vision import conditional_merge_vision_mask, detect_image_resolution, extract_vision_mask, pack_resolution, read_static_image, read_static_images, restrict_trim_video_frame, scale_resolution, write_image
from facefusion.workflows.core import clear, is_process_stopping, setup


def process(start_time : float) -> ErrorCode:
	tasks =\
	[
		analyse_image,
		clear,
		setup,
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


def process_image() -> ErrorCode:
	state_manager.set_item('output_video_fps', 25.0) # TODO: set default fps value
	source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
	trim_frame_start, trim_frame_end = restrict_trim_audio_frame(source_audio_path, state_manager.get_item('output_video_fps'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
	audio_frame_total = trim_frame_end - trim_frame_start
	temp_frame_paths = get_temp_sequence_paths(state_manager.get_item('temp_path'), state_manager.get_item('output_path'), audio_frame_total, '%08d', state_manager.get_item('temp_frame_format'))

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


def process_temp_frame(temp_frame_path : str, frame_number : int) -> bool:  # TODO refinement like to_video.py file.
	output_video_fps = state_manager.get_item('output_video_fps')
	reference_vision_frame = read_static_image(state_manager.get_item('target_path'))
	source_vision_frames = read_static_images(state_manager.get_item('source_paths'))
	source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
	target_vision_frame = read_static_image(state_manager.get_item('target_path'), 'rgba')
	temp_vision_frame = target_vision_frame.copy()
	temp_vision_mask = extract_vision_mask(temp_vision_frame)

	source_audio_frame = get_audio_frame(source_audio_path, output_video_fps, frame_number)
	source_voice_frame = get_voice_frame(source_audio_path, output_video_fps, frame_number)

	if not numpy.any(source_audio_frame):
		source_audio_frame = create_empty_audio_frame()
	if not numpy.any(source_voice_frame):
		source_voice_frame = create_empty_audio_frame()

	for processor_module in get_processors_modules(state_manager.get_item('processors')):
		temp_vision_frame, temp_vision_mask = processor_module.process_frame(
		{
			'reference_vision_frame': reference_vision_frame,
			'source_vision_frames': source_vision_frames,
			'source_audio_frame': source_audio_frame,
			'source_voice_frame': source_voice_frame,
			'target_vision_frame': target_vision_frame[:, :, :3],
			'temp_vision_frame': temp_vision_frame[:, :, :3],
			'temp_vision_mask': temp_vision_mask
		})

	temp_vision_frame = conditional_merge_vision_mask(temp_vision_frame, temp_vision_mask)
	return write_image(temp_frame_path, temp_vision_frame)


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
		move_temp_file(state_manager.get_item('temp_path'), state_manager.get_item('output_path'))
	else:
		source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
		if source_audio_path:
			if ffmpeg.replace_audio(source_audio_path, state_manager.get_item('output_path')):
				logger.debug(translator.get('replacing_audio_succeeded'), __name__)
			else:
				if is_process_stopping():
					return 4
				logger.warn(translator.get('replacing_audio_skipped'), __name__)
				move_temp_file(state_manager.get_item('temp_path'), state_manager.get_item('output_path'))
	return 0


def finalize_video(start_time : float) -> ErrorCode:
	if is_video(state_manager.get_item('output_path')):
		logger.info(translator.get('processing_video_succeeded').format(seconds = calculate_end_time(start_time)), __name__)
	else:
		logger.error(translator.get('processing_video_failed'), __name__)
		return 1
	return 0
