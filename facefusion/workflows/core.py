from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import numpy
from tqdm import tqdm

import facefusion.workflows.image_to_video as image_to_video
from facefusion import ffprobe, logger, process_manager, state_manager, translator, video_manager
from facefusion.audio import create_empty_audio_frame, get_audio_frame, get_voice_frame
from facefusion.common_helper import get_first
from facefusion.filesystem import filter_audio_paths
from facefusion.processors.core import get_processors_modules
from facefusion.temp_helper import clear_temp_directory, create_temp_directory, resolve_temp_frame_set
from facefusion.types import AudioFrame, ErrorCode, VisionFrame
from facefusion.vision import conditional_merge_vision_mask, detect_video_resolution, extract_vision_mask, read_static_image, read_static_images, read_static_video_frame, restrict_trim_frame, restrict_video_fps, restrict_video_resolution, scale_resolution


def is_process_stopping() -> bool:
	if process_manager.is_stopping():
		process_manager.end()
		logger.info(translator.get('processing_stopped'), __name__)
	return process_manager.is_pending()


def setup() -> ErrorCode:
	if create_temp_directory(state_manager.get_item('target_path')):
		logger.debug(translator.get('creating_temp'), __name__)
	return 0


def clear() -> ErrorCode:
	if clear_temp_directory(state_manager.get_item('target_path')):
		logger.debug(translator.get('clearing_temp'), __name__)
	return 0


#todo: copy - renamed workflow to workflow_mode
def conditional_get_reference_vision_frame() -> VisionFrame:
	if state_manager.get_item('workflow_mode') == 'image-to-video':
		return read_static_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))
	return read_static_image(state_manager.get_item('target_path'))


#todo: copy - renamed workflow to workflow_mode, video only, trim offset
def conditional_get_source_audio_frame(frame_number : int) -> AudioFrame:
	if state_manager.get_item('workflow_mode') == 'image-to-video':
		trim_frame_start, _ = restrict_trim_frame(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
		temp_video_fps = restrict_video_fps(state_manager.get_item('target_path'), state_manager.get_item('output_video_fps'))
		source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
		source_audio_frame = get_audio_frame(source_audio_path, temp_video_fps, frame_number - trim_frame_start)

		if numpy.any(source_audio_frame):
			return source_audio_frame

	return create_empty_audio_frame()


#todo: copy - renamed workflow to workflow_mode, video only, trim offset
def conditional_get_source_voice_frame(frame_number : int) -> AudioFrame:
	if state_manager.get_item('workflow_mode') == 'image-to-video':
		trim_frame_start, _ = restrict_trim_frame(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
		temp_video_fps = restrict_video_fps(state_manager.get_item('target_path'), state_manager.get_item('output_video_fps'))
		source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
		source_voice_frame = get_voice_frame(source_audio_path, temp_video_fps, frame_number - trim_frame_start)

		if numpy.any(source_voice_frame):
			return source_voice_frame

	return create_empty_audio_frame()


#todo: needs review - [workflow] [critical: medium] copy of process_temp_frame, receives vision frames instead of paths
def process_target_frame(frame_number : int, target_vision_frames : List[VisionFrame], temp_vision_frame : VisionFrame) -> VisionFrame:
	reference_vision_frame = conditional_get_reference_vision_frame()
	source_vision_frames = read_static_images(state_manager.get_item('source_paths'))
	source_audio_frame = conditional_get_source_audio_frame(frame_number)
	source_voice_frame = conditional_get_source_voice_frame(frame_number)
	temp_vision_mask = extract_vision_mask(temp_vision_frame)

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


#todo: needs review - [workflow] [critical: medium] copy of process_frames, uses temp_frame_set and warms the reference frame
def process_disk_frames() -> ErrorCode:
	temp_frame_set = resolve_temp_frame_set(state_manager.get_item('target_path'))

	if temp_frame_set:
		with tqdm(total = len(temp_frame_set), desc = translator.get('processing'), unit = 'frame', ascii = ' =', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
			progress.set_postfix(execution_providers = state_manager.get_item('execution_providers'))

			read_static_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))

			with ThreadPoolExecutor(max_workers = state_manager.get_item('execution_thread_count')) as executor:
				futures = []

				for frame_number, temp_frame_path in temp_frame_set.items():
					future = executor.submit(image_to_video.process_disk_frame, temp_frame_path, frame_number, temp_frame_set)
					futures.append(future)

				for future in as_completed(futures):
					if is_process_stopping():
						for pending_future in futures:
							pending_future.cancel()

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
		frame_look_ahead = image_to_video.calculate_frame_look_ahead(temp_video_resolution)

		with tqdm(total = len(frame_range), desc = translator.get('processing'), unit = 'frame', ascii = ' =', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
			progress.set_postfix(execution_providers = state_manager.get_item('execution_providers'))

			read_static_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))

			with ThreadPoolExecutor(max_workers = state_manager.get_item('execution_thread_count')) as executor:
				futures = []

				for frame_number in frame_range:
					future = executor.submit(image_to_video.process_stream_frame, frame_number, temp_video_resolution)
					futures.append(future)

					if len(futures) > frame_look_ahead:
						image_to_video.write_stream_frame(video_writer, futures, progress)

				for _ in list(futures):
					image_to_video.write_stream_frame(video_writer, futures, progress)

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
