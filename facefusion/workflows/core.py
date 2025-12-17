from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy
from tqdm import tqdm

from facefusion import content_analyser, logger, process_manager, state_manager, translator
from facefusion.audio import create_empty_audio_frame, get_audio_frame, get_voice_frame
from facefusion.common_helper import get_first
from facefusion.filesystem import filter_audio_paths
from facefusion.processors.core import get_processors_modules
from facefusion.temp_helper import clear_temp_directory, create_temp_directory, resolve_temp_frame_paths
from facefusion.types import AudioFrame, ErrorCode, VisionFrame
from facefusion.vision import conditional_merge_vision_mask, extract_vision_mask, read_static_image, read_static_images, read_static_video_frame, restrict_video_fps, write_image


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


def analyse_image() -> ErrorCode:
	if content_analyser.analyse_image(state_manager.get_item('target_path')):
		return 3
	return 0


def conditional_get_source_audio_frame(frame_number : int) -> AudioFrame:
	if state_manager.get_item('workflow') in [ 'audio-to-image:video', 'image-to-video' ]:
		source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
		output_video_fps = state_manager.get_item('output_video_fps')

		if state_manager.get_item('workflow') == 'image-to-video':
			output_video_fps = restrict_video_fps(state_manager.get_item('target_path'), output_video_fps)
		source_audio_frame = get_audio_frame(source_audio_path, output_video_fps, frame_number)

		if numpy.any(source_audio_frame):
			return source_audio_frame

	return create_empty_audio_frame()


def conditional_get_source_voice_frame(frame_number: int) -> AudioFrame:
	if state_manager.get_item('workflow') in [ 'audio-to-image:video', 'image-to-video' ]:
		source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
		output_video_fps = state_manager.get_item('output_video_fps')

		if state_manager.get_item('workflow') == 'image-to-video':
			output_video_fps = restrict_video_fps(state_manager.get_item('target_path'), output_video_fps)
		source_voice_frame = get_voice_frame(source_audio_path, output_video_fps, frame_number)

		if numpy.any(source_voice_frame):
			return source_voice_frame

	return create_empty_audio_frame()


def conditional_get_reference_vision_frame() -> VisionFrame:
	if state_manager.get_item('workflow') in [ 'image-to-video', 'image-to-video:frames' ]:
		return read_static_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))
	return read_static_image(state_manager.get_item('target_path'))


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


def process_frames() -> ErrorCode:
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
