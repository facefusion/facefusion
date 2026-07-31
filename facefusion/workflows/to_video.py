from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Deque

import cv2
import numpy
from tqdm import tqdm

from facefusion import content_analyser, ffmpeg, logger, process_manager, state_manager, translator, video_manager
from facefusion.common_helper import get_first, get_middle
from facefusion.filesystem import filter_audio_paths, is_video
from facefusion.processors.core import get_processors_modules
from facefusion.temp_helper import move_temp_file, resolve_temp_frame_set
from facefusion.time_helper import calculate_end_time
from facefusion.types import ErrorCode, Resolution, VisionFrame
from facefusion.vision import detect_video_resolution, pack_resolution, read_static_image, read_static_video_frame, restrict_trim_frame, restrict_video_fps, restrict_video_resolution, scale_resolution, select_video_frames, write_image
from facefusion.workflows.core import conditional_get_target_vision_frames, is_process_stopping, process_temp_frame


def analyse_video() -> ErrorCode:
	trim_frame_start, trim_frame_end = restrict_trim_frame(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))

	if content_analyser.analyse_video(state_manager.get_item('target_path'), trim_frame_start, trim_frame_end):
		return 3
	return 0


def extract_frames() -> ErrorCode:
	trim_frame_start, trim_frame_end = restrict_trim_frame(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
	output_video_resolution = scale_resolution(detect_video_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_video_scale'))
	temp_video_resolution = restrict_video_resolution(state_manager.get_item('target_path'), output_video_resolution)
	temp_video_fps = restrict_video_fps(state_manager.get_item('target_path'), state_manager.get_item('output_video_fps'))
	logger.info(translator.get('extracting_frames').format(resolution=pack_resolution(temp_video_resolution), fps=temp_video_fps), __name__)

	if ffmpeg.extract_frames(state_manager.get_item('target_path'), temp_video_resolution, temp_video_fps, trim_frame_start, trim_frame_end):
		logger.debug(translator.get('extracting_frames_succeeded'), __name__)
	else:
		if is_process_stopping():
			return 4
		logger.error(translator.get('extracting_frames_failed'), __name__)
		return 1
	return 0


def process_disk_frame(temp_frame_path : str, frame_number : int) -> bool:
	target_vision_frames = conditional_get_target_vision_frames(frame_number)
	temp_vision_frame = read_static_image(temp_frame_path, 'rgba')
	temp_vision_frame = process_temp_frame(target_vision_frames, temp_vision_frame, frame_number)
	return write_image(temp_frame_path, temp_vision_frame)


def process_disk_frames() -> ErrorCode:
	temp_frame_set = resolve_temp_frame_set(state_manager.get_item('target_path'))

	if temp_frame_set:
		with tqdm(total = len(temp_frame_set), desc = translator.get('processing'), unit = 'frame', ascii = ' =', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
			progress.set_postfix(execution_providers = state_manager.get_item('execution_providers'))

			read_static_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))

			with ThreadPoolExecutor(max_workers = state_manager.get_item('execution_thread_count')) as executor:
				futures : Deque[Future[bool]] = deque()

				for frame_number, temp_frame_path in temp_frame_set.items():
					future = executor.submit(process_disk_frame, temp_frame_path, frame_number)
					futures.append(future)

				while futures:
					future = futures.popleft()

					if is_process_stopping():

						for pending_future in futures:
							pending_future.cancel()

						futures.clear()

					else:
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


def process_memory_frame(frame_number : int, temp_video_resolution : Resolution) -> VisionFrame:
	target_vision_frames = select_video_frames(state_manager.get_item('target_path'), frame_number, state_manager.get_item('target_frame_amount'))
	target_vision_frame = get_middle(target_vision_frames)
	temp_vision_frame = target_vision_frame.copy()

	if not (target_vision_frame.shape[1], target_vision_frame.shape[0]) == temp_video_resolution:
		temp_vision_frame = cv2.resize(target_vision_frame, temp_video_resolution)

	temp_vision_frame = process_temp_frame(target_vision_frames, temp_vision_frame, frame_number)

	if state_manager.get_item('temp_pixel_format') == 'bgra':
		temp_vision_frame = cv2.cvtColor(temp_vision_frame, cv2.COLOR_BGR2BGRA)

	if state_manager.get_item('temp_pixel_format') == 'bgr24':
		temp_vision_frame = temp_vision_frame[:, :, :3]

	return numpy.ascontiguousarray(temp_vision_frame)


def process_memory_frames() -> ErrorCode:
	trim_frame_start, trim_frame_end = restrict_trim_frame(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
	output_video_resolution = scale_resolution(detect_video_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_video_scale'))
	temp_video_resolution = restrict_video_resolution(state_manager.get_item('target_path'), output_video_resolution)
	temp_video_fps = restrict_video_fps(state_manager.get_item('target_path'), state_manager.get_item('output_video_fps'))
	temp_frame_range = range(trim_frame_start, trim_frame_end)

	if temp_frame_range:
		video_writer = video_manager.get_writer(state_manager.get_item('target_path'), temp_video_fps, temp_video_resolution, output_video_resolution, state_manager.get_item('output_video_fps'))

		with tqdm(total = len(temp_frame_range), desc = translator.get('processing'), unit = 'frame', ascii = ' =', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
			progress.set_postfix(execution_providers = state_manager.get_item('execution_providers'))

			read_static_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))

			with ThreadPoolExecutor(max_workers = state_manager.get_item('execution_thread_count')) as executor:
				futures : Deque[Future[VisionFrame]] = deque()

				for frame_number in temp_frame_range:
					future = executor.submit(process_memory_frame, frame_number, temp_video_resolution)
					futures.append(future)

				while futures:
					future = futures.popleft()

					if is_process_stopping():

						for pending_future in futures:
							pending_future.cancel()

						futures.clear()

					else:
						video_manager.write_video_frame(video_writer, future.result())
						progress.update()

		if not video_manager.close_video_writer(video_writer):
			process_manager.stop()

		for processor_module in get_processors_modules(state_manager.get_item('processors')):
			processor_module.post_process()

		if is_process_stopping():
			return 4
	else:
		logger.error(translator.get('temp_frames_not_found'), __name__)
		return 1
	return 0


def merge_frames() -> ErrorCode:
	trim_frame_start, trim_frame_end = restrict_trim_frame(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
	output_video_resolution = scale_resolution(detect_video_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_video_scale'))
	temp_video_fps = restrict_video_fps(state_manager.get_item('target_path'), state_manager.get_item('output_video_fps'))

	logger.info(translator.get('merging_video').format(resolution = pack_resolution(output_video_resolution), fps = state_manager.get_item('output_video_fps')), __name__)
	if ffmpeg.merge_video(state_manager.get_item('target_path'), temp_video_fps, output_video_resolution, state_manager.get_item('output_video_fps'), trim_frame_start, trim_frame_end):
		logger.debug(translator.get('merging_video_succeeded'), __name__)
	else:
		if is_process_stopping():
			return 4
		logger.error(translator.get('merging_video_failed'), __name__)
		return 1
	return 0


def restore_audio() -> ErrorCode:
	trim_frame_start, trim_frame_end = restrict_trim_frame(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))

	if state_manager.get_item('output_audio_volume') == 0:
		logger.info(translator.get('skipping_audio'), __name__)
		move_temp_file(state_manager.get_item('target_path'), state_manager.get_item('output_path'))
	else:
		source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
		if source_audio_path:
			if ffmpeg.replace_audio(state_manager.get_item('target_path'), source_audio_path, state_manager.get_item('output_path')):
				video_manager.clear_video_pool()
				logger.debug(translator.get('replacing_audio_succeeded'), __name__)
			else:
				video_manager.clear_video_pool()
				if is_process_stopping():
					return 4
				logger.warn(translator.get('replacing_audio_skipped'), __name__)
				move_temp_file(state_manager.get_item('target_path'), state_manager.get_item('output_path'))
		else:
			if ffmpeg.restore_audio(state_manager.get_item('target_path'), state_manager.get_item('output_path'), trim_frame_start, trim_frame_end):
				video_manager.clear_video_pool()
				logger.debug(translator.get('restoring_audio_succeeded'), __name__)
			else:
				video_manager.clear_video_pool()
				if is_process_stopping():
					return 4
				logger.warn(translator.get('restoring_audio_skipped'), __name__)
				move_temp_file(state_manager.get_item('target_path'), state_manager.get_item('output_path'))
	return 0


def finalize_video(start_time : float) -> ErrorCode:
	if is_video(state_manager.get_item('output_path')):
		logger.info(translator.get('processing_video_succeeded').format(seconds = calculate_end_time(start_time)), __name__)
	else:
		logger.error(translator.get('processing_video_failed'), __name__)
		return 1
	return 0
