from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from functools import partial
from typing import List, Tuple

import cv2
import numpy
from tqdm import tqdm

from facefusion import content_analyser, ffmpeg, ffprobe, logger, process_manager, state_manager, translator, video_manager
from facefusion.audio import create_empty_audio_frame, get_audio_frame, get_voice_frame
from facefusion.common_helper import get_first, get_middle
from facefusion.filesystem import filter_audio_paths, is_video
from facefusion.processors.core import get_processors_modules
from facefusion.temp_helper import move_temp_file, resolve_temp_frame_set
from facefusion.time_helper import calculate_end_time
from facefusion.types import ErrorCode, FrameSet, Resolution, VideoWriter, VisionFrame
from facefusion.vision import conditional_merge_vision_mask, detect_video_resolution, extract_vision_mask, pack_resolution, read_static_image, read_static_images, read_static_video_frame, restrict_trim_frame, restrict_video_fps, restrict_video_resolution, scale_resolution, select_video_frames, write_image
from facefusion.workflows.core import clear, is_process_stopping, setup


def process(start_time : float) -> ErrorCode:
	tasks =\
	[
		analyse_video,
		clear,
		setup
	]

	if state_manager.get_item('workflow_strategy') == 'disk':
		tasks.extend(
		[
			extract_frames,
			process_frames,
			merge_frames
		])

	if state_manager.get_item('workflow_strategy') == 'stream':
		tasks.append(process_stream_frames)

	tasks.extend(
	[
		restore_audio,
		partial(finalize_video, start_time),
		clear
	])
	process_manager.start()

	for task in tasks:
		error_code = task() #type:ignore[operator]

		if error_code > 0:
			process_manager.end()
			return error_code

	process_manager.end()
	return 0


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


#todo: needs review - [workflow] [critical: medium] warms the reference frame before the executor, neighbors come from temp frames
def process_frames() -> ErrorCode:
	temp_frame_set = resolve_temp_frame_set(state_manager.get_item('target_path'))

	if temp_frame_set:
		with tqdm(total = len(temp_frame_set), desc = translator.get('processing'), unit = 'frame', ascii = ' =', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
			progress.set_postfix(execution_providers = state_manager.get_item('execution_providers'))

			read_static_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))

			with ThreadPoolExecutor(max_workers = state_manager.get_item('execution_thread_count')) as executor:
				futures = []

				for frame_number, temp_frame_path in temp_frame_set.items():
					future = executor.submit(process_disk_frame, temp_frame_path, frame_number, temp_frame_set)
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


#todo: needs review - [workflow] [critical: medium] shared processing path for disk and stream, receives vision frames instead of paths
def process_target_frame(frame_number : int, target_vision_frames : List[VisionFrame], temp_vision_frame : VisionFrame) -> VisionFrame:
	trim_frame_start, _ = restrict_trim_frame(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
	reference_vision_frame = read_static_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))
	source_vision_frames = read_static_images(state_manager.get_item('source_paths'))
	source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
	temp_video_fps = restrict_video_fps(state_manager.get_item('target_path'), state_manager.get_item('output_video_fps'))
	temp_vision_mask = extract_vision_mask(temp_vision_frame)

	source_audio_frame = get_audio_frame(source_audio_path, temp_video_fps, frame_number - trim_frame_start)
	source_voice_frame = get_voice_frame(source_audio_path, temp_video_fps, frame_number - trim_frame_start)

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
			'target_vision_frames': target_vision_frames,
			'temp_vision_frame': temp_vision_frame[:, :, :3],
			'temp_vision_mask': temp_vision_mask
		})

	return conditional_merge_vision_mask(temp_vision_frame, temp_vision_mask)


#todo: needs review - [correctness] [critical: high] missing neighbor frames resolve to none paths and rely on read_static_image returning none
def resolve_temp_vision_frames(frame_number : int, frame_amount : int, temp_frame_set : FrameSet) -> List[VisionFrame]:
	temp_vision_frames = []
	frame_range = range(frame_number - frame_amount, frame_number + frame_amount + 1)

	for temp_frame_number in frame_range:
		temp_vision_frames.append(read_static_image(temp_frame_set.get(temp_frame_number)))

	return temp_vision_frames


#todo: needs review - [workflow] [critical: low] disk variant reads temp frame and neighbors from disk and writes back in place
def process_disk_frame(temp_frame_path : str, frame_number : int, temp_frame_set : FrameSet) -> bool:
	target_vision_frames = resolve_temp_vision_frames(frame_number, state_manager.get_item('target_frame_amount'), temp_frame_set)
	temp_vision_frame = read_static_image(temp_frame_path, 'rgba')
	temp_vision_frame = process_target_frame(frame_number, target_vision_frames, temp_vision_frame)
	return write_image(temp_frame_path, temp_vision_frame)


#todo: needs review - [memory] [critical: high] frame look ahead bound by a hardcoded 3gb budget
def calculate_frame_look_ahead(temp_video_resolution : Resolution) -> int:
	width, height = temp_video_resolution
	frame_memory_budget = 3 * 1024 ** 3
	frame_memory_usage = width * height * 4 * 6
	return min(state_manager.get_item('execution_thread_count') * 2, max(2, frame_memory_budget // frame_memory_usage))


#todo: needs review - [streaming] [critical: high] middle frame resized to temp resolution before processing, channels follow temp_pixel_format to match the writer pipe
def process_stream_frame(frame_number : int, temp_video_resolution : Resolution) -> Tuple[int, VisionFrame]:
	target_vision_frames = select_video_frames(state_manager.get_item('target_path'), frame_number, state_manager.get_item('target_frame_amount'))
	target_vision_frame = get_middle(target_vision_frames)
	temp_vision_frame = target_vision_frame.copy()

	if not (target_vision_frame.shape[1], target_vision_frame.shape[0]) == temp_video_resolution:
		temp_vision_frame = cv2.resize(target_vision_frame, temp_video_resolution)
	temp_vision_frame = process_target_frame(frame_number, target_vision_frames, temp_vision_frame)

	if state_manager.get_item('temp_pixel_format') == 'bgra':
		temp_vision_frame = cv2.cvtColor(temp_vision_frame, cv2.COLOR_BGR2BGRA)

	if state_manager.get_item('temp_pixel_format') == 'bgr24':
		temp_vision_frame = temp_vision_frame[:, :, :3]

	return frame_number, numpy.ascontiguousarray(temp_vision_frame)


#todo: needs review - [streaming] [critical: high] ordered submit and drain keeps writes in order, failed close stops the process manager
def process_stream_frames() -> ErrorCode:
	trim_frame_start, trim_frame_end = restrict_trim_frame(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
	output_video_resolution = scale_resolution(detect_video_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_video_scale'))
	temp_video_resolution = restrict_video_resolution(state_manager.get_item('target_path'), output_video_resolution)
	temp_video_fps = restrict_video_fps(state_manager.get_item('target_path'), state_manager.get_item('output_video_fps'))
	frame_range = range(trim_frame_start, trim_frame_end)

	if frame_range:
		video_metadata = ffprobe.extract_static_video_metadata(state_manager.get_item('target_path'))
		video_writer = video_manager.get_writer(state_manager.get_item('target_path'), video_metadata, temp_video_fps, temp_video_resolution, output_video_resolution, state_manager.get_item('output_video_fps'))
		frame_look_ahead = calculate_frame_look_ahead(temp_video_resolution)

		with tqdm(total = len(frame_range), desc = translator.get('processing'), unit = 'frame', ascii = ' =', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
			progress.set_postfix(execution_providers = state_manager.get_item('execution_providers'))

			read_static_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))

			with ThreadPoolExecutor(max_workers = state_manager.get_item('execution_thread_count')) as executor:
				futures = []

				for frame_number in frame_range:
					futures.append(executor.submit(process_stream_frame, frame_number, temp_video_resolution))
					write_stream_frames(video_writer, futures, frame_look_ahead, progress)

				write_stream_frames(video_writer, futures, 1, progress)

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


#todo: needs review - [streaming] [critical: medium] drains futures down to the look ahead, stopping skips writes without cancelling
def write_stream_frames(video_writer : VideoWriter, futures : List[Future[Tuple[int, VisionFrame]]], frame_look_ahead : int, progress : tqdm) -> None:
	for _ in range(len(futures) - frame_look_ahead + 1):
		if not is_process_stopping():
			_, temp_vision_frame = futures.pop(0).result()
			video_manager.write_video_writer_frame(video_writer, temp_vision_frame)
			progress.update()


def finalize_video(start_time : float) -> ErrorCode:
	if is_video(state_manager.get_item('output_path')):
		logger.info(translator.get('processing_video_succeeded').format(seconds = calculate_end_time(start_time)), __name__)
	else:
		logger.error(translator.get('processing_video_failed'), __name__)
		return 1
	return 0
