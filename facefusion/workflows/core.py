from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Deque, List

import numpy

from facefusion import cli_progress, logger, process_manager, state_manager, translator
from facefusion.audio import create_empty_audio_frame, get_audio_frame, get_voice_frame
from facefusion.common_helper import get_first
from facefusion.filesystem import filter_audio_paths, get_file_extension, has_audio, has_image, has_video
from facefusion.processors.core import get_processors_modules
from facefusion.temp_helper import clear_temp_directory, create_temp_directory, resolve_temp_frame_set
from facefusion.types import AudioFrame, ErrorCode, VisionFrame, WorkflowMode
from facefusion.vision import conditional_merge_vision_mask, extract_vision_mask, read_static_image, read_static_images, read_static_video_frame, restrict_trim_video_frame, restrict_video_fps, select_video_frames, write_image


def detect_workflow_mode() -> WorkflowMode:
	target_path = state_manager.get_item('target_path')
	output_path = state_manager.get_item('output_path')

	if has_video([ target_path ]):
		if get_file_extension(output_path):
			return 'image-to-video'
		return 'image-to-video:frames'

	if has_audio(state_manager.get_item('source_paths')) and has_image([ target_path ]):
		if get_file_extension(output_path):
			return 'audio-to-image:video'
		return 'audio-to-image:frames'

	return 'image-to-image'


def is_process_stopping() -> bool:
	if process_manager.is_stopping():
		process_manager.end()
		logger.info(translator.get('processing_stopped'), __name__)
	return process_manager.is_pending()


def setup() -> ErrorCode:
	if create_temp_directory(state_manager.get_temp_path(), state_manager.get_item('output_path')):
		logger.debug(translator.get('creating_temp'), __name__)
	return 0


def clear() -> ErrorCode:
	if clear_temp_directory(state_manager.get_temp_path(), state_manager.get_item('output_path')):
		logger.debug(translator.get('clearing_temp'), __name__)
	return 0


def conditional_get_source_audio_frame(frame_number : int) -> AudioFrame:
	if state_manager.get_item('workflow_mode') in [ 'audio-to-image:frames', 'audio-to-image:video', 'image-to-video' ]:
		source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
		fps = state_manager.get_item('output_audio_fps')

		if state_manager.get_item('workflow_mode') == 'image-to-video':
			trim_frame_start, _ = restrict_trim_video_frame(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
			fps = restrict_video_fps(state_manager.get_item('target_path'), state_manager.get_item('output_video_fps'))
			frame_number = frame_number - trim_frame_start

		source_audio_frame = get_audio_frame(source_audio_path, fps, frame_number)

		if numpy.any(source_audio_frame):
			return source_audio_frame

	return create_empty_audio_frame()


def conditional_get_source_voice_frame(frame_number : int) -> AudioFrame:
	if state_manager.get_item('workflow_mode') in [ 'audio-to-image:frames', 'audio-to-image:video', 'image-to-video' ]:
		source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
		temp_fps = state_manager.get_item('output_audio_fps')

		if state_manager.get_item('workflow_mode') == 'image-to-video':
			trim_frame_start, _ = restrict_trim_video_frame(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
			temp_fps = restrict_video_fps(state_manager.get_item('target_path'), state_manager.get_item('output_video_fps'))
			frame_number = frame_number - trim_frame_start

		source_voice_frame = get_voice_frame(source_audio_path, temp_fps, frame_number)

		if numpy.any(source_voice_frame):
			return source_voice_frame

	return create_empty_audio_frame()


def conditional_get_reference_vision_frame() -> VisionFrame:
	if state_manager.get_item('workflow_mode') in [ 'image-to-video', 'image-to-video:frames' ]:
		return read_static_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))
	return read_static_image(state_manager.get_item('target_path'))


def conditional_get_target_vision_frames(frame_number : int) -> List[VisionFrame]:
	if state_manager.get_item('workflow_mode') in [ 'image-to-video', 'image-to-video:frames' ]:
		return select_video_frames(state_manager.get_item('target_path'), frame_number, state_manager.get_item('target_frame_amount'))
	return [ read_static_image(state_manager.get_item('target_path')) ]


def process_temp_frame(temp_frame_path : str, frame_number : int) -> bool:
	reference_vision_frame = conditional_get_reference_vision_frame()
	source_vision_frames = read_static_images(state_manager.get_item('source_paths'))
	source_audio_frame = conditional_get_source_audio_frame(frame_number)
	source_voice_frame = conditional_get_source_voice_frame(frame_number)
	target_vision_frames = conditional_get_target_vision_frames(frame_number)
	temp_vision_frame = read_static_image(temp_frame_path, 'rgba').copy()
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

	temp_vision_frame = conditional_merge_vision_mask(temp_vision_frame, temp_vision_mask)
	return write_image(temp_frame_path, temp_vision_frame)


def process_temp_vision_frame(target_vision_frames : List[VisionFrame], temp_vision_frame : VisionFrame, frame_number : int) -> VisionFrame:
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


def process_frames() -> ErrorCode:
	temp_frame_set = resolve_temp_frame_set(state_manager.get_temp_path(), state_manager.get_item('output_path'), state_manager.get_item('temp_frame_format'))

	if temp_frame_set:
		with cli_progress.create(frame = 'mode') as progress:
			progress.set_title(translator.get('processing'))
			progress.count(temp_frame_set)

			with ThreadPoolExecutor(max_workers = state_manager.get_item('execution_thread_count')) as executor:
				futures : Deque[Future[bool]] = deque()

				for frame_number, temp_frame_path in temp_frame_set.items():
					future = executor.submit(process_temp_frame, temp_frame_path, frame_number)
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
