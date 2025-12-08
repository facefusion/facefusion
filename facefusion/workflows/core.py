from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy
from tqdm import tqdm

from facefusion import ffmpeg, logger, process_manager, state_manager, translator, video_manager
from facefusion.audio import create_empty_audio_frame, get_audio_frame, get_voice_frame
from facefusion.common_helper import get_first
from facefusion.filesystem import filter_audio_paths, is_video
from facefusion.media_helper import restrict_trim_frame
from facefusion.processors.core import get_processors_modules
from facefusion.temp_helper import clear_temp_directory, create_temp_directory, move_temp_file, resolve_temp_frame_paths
from facefusion.time_helper import calculate_end_time
from facefusion.types import AudioFrame, ErrorCode, Fps, Resolution, VisionFrame
from facefusion.vision import conditional_merge_vision_mask, detect_image_resolution, detect_video_resolution, extract_vision_mask, pack_resolution, read_static_image, read_static_images, read_static_video_frame, restrict_video_fps, scale_resolution, write_image


def is_process_stopping() -> bool:
	if process_manager.is_stopping():
		process_manager.end()
		logger.info(translator.get('processing_stopped'), __name__)
	return process_manager.is_pending()


def setup() -> ErrorCode:
	create_temp_directory(state_manager.get_temp_path(), state_manager.get_item('output_path'))
	logger.debug(translator.get('creating_temp'), __name__)
	return 0


def clear() -> ErrorCode:
	clear_temp_directory(state_manager.get_temp_path(), state_manager.get_item('output_path'))
	logger.debug(translator.get('clearing_temp'), __name__)
	return 0


def conditional_get_source_audio_frame(frame_number : int) -> AudioFrame:
	if state_manager.get_item('workflow') in [ 'audio-to-image', 'image-to-video' ]:
		source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
		output_video_fps = state_manager.get_item('output_video_fps')

		if state_manager.get_item('workflow') == 'image-to-video':
			output_video_fps = restrict_video_fps(state_manager.get_item('target_path'), output_video_fps)
		source_audio_frame = get_audio_frame(source_audio_path, output_video_fps, frame_number)

		if numpy.any(source_audio_frame):
			return source_audio_frame

	return create_empty_audio_frame()


def conditional_get_source_voice_frame(frame_number: int) -> AudioFrame:
	if state_manager.get_item('workflow') in [ 'audio-to-image', 'image-to-video' ]:
		source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
		output_video_fps = state_manager.get_item('output_video_fps')

		if state_manager.get_item('workflow') == 'image-to-video':
			output_video_fps = restrict_video_fps(state_manager.get_item('target_path'), output_video_fps)
		source_voice_frame = get_voice_frame(source_audio_path, output_video_fps, frame_number)

		if numpy.any(source_voice_frame):
			return source_voice_frame

	return create_empty_audio_frame()


def conditional_get_reference_vision_frame() -> VisionFrame:
	if state_manager.get_item('workflow') == 'image-to-video':
		return read_static_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))
	return read_static_image(state_manager.get_item('target_path'))


def conditional_scale_resolution() -> Resolution:
	if state_manager.get_item('workflow') == 'image-to-video':
		return scale_resolution(detect_video_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_video_scale'))
	return scale_resolution(detect_image_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_video_scale'))


def conditional_restrict_video_fps() -> Fps:
	if state_manager.get_item('workflow') == 'image-to-video':
		return restrict_video_fps(state_manager.get_item('target_path'), state_manager.get_item('output_video_fps'))
	return state_manager.get_item('output_video_fps')


def conditional_clear_video_pool() -> None:
	if state_manager.get_item('workflow') == 'image-to-video':
		video_manager.clear_video_pool()


def process_temp_frame(temp_frame_path : str, frame_number : int) -> bool:
	reference_vision_frame = conditional_get_reference_vision_frame()
	source_vision_frames = read_static_images(state_manager.get_item('source_paths'))
	target_vision_frame = read_static_image(temp_frame_path, 'rgba')
	source_audio_frame = conditional_get_source_audio_frame(frame_number)
	source_voice_frame = conditional_get_source_voice_frame(frame_number)
	temp_vision_frame = target_vision_frame.copy()
	temp_vision_mask = extract_vision_mask(temp_vision_frame)

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


def process_video() -> ErrorCode:
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
