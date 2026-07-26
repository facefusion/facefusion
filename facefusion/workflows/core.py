from typing import List

import numpy

from facefusion import logger, process_manager, state_manager, translator
from facefusion.audio import create_empty_audio_frame, get_audio_frame, get_voice_frame
from facefusion.common_helper import get_first
from facefusion.filesystem import filter_audio_paths
from facefusion.processors.core import get_processors_modules
from facefusion.temp_helper import clear_temp_directory, create_temp_directory
from facefusion.types import AudioFrame, ErrorCode, VisionFrame
from facefusion.vision import conditional_merge_vision_mask, extract_vision_mask, read_static_image, read_static_images, read_static_video_frame, restrict_trim_frame, restrict_video_fps, select_video_frames


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


def conditional_get_reference_vision_frame() -> VisionFrame:
	if state_manager.get_item('workflow_mode') == 'image-to-video':
		return read_static_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))
	return read_static_image(state_manager.get_item('target_path'))


def conditional_get_source_audio_frame(frame_number : int) -> AudioFrame:
	if state_manager.get_item('workflow_mode') == 'image-to-video':
		trim_frame_start, _ = restrict_trim_frame(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
		temp_video_fps = restrict_video_fps(state_manager.get_item('target_path'), state_manager.get_item('output_video_fps'))
		source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
		source_audio_frame = get_audio_frame(source_audio_path, temp_video_fps, frame_number - trim_frame_start)

		if numpy.any(source_audio_frame):
			return source_audio_frame

	return create_empty_audio_frame()


def conditional_get_source_voice_frame(frame_number : int) -> AudioFrame:
	if state_manager.get_item('workflow_mode') == 'image-to-video':
		trim_frame_start, _ = restrict_trim_frame(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
		temp_video_fps = restrict_video_fps(state_manager.get_item('target_path'), state_manager.get_item('output_video_fps'))
		source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
		source_voice_frame = get_voice_frame(source_audio_path, temp_video_fps, frame_number - trim_frame_start)

		if numpy.any(source_voice_frame):
			return source_voice_frame

	return create_empty_audio_frame()


def conditional_get_target_vision_frames(frame_number : int) -> List[VisionFrame]:
	if state_manager.get_item('workflow_mode') == 'image-to-video':
		return select_video_frames(state_manager.get_item('target_path'), frame_number, state_manager.get_item('target_frame_amount'))
	return [ read_static_image(state_manager.get_item('target_path')) ]


def process_temp_frame(target_vision_frames : List[VisionFrame], temp_vision_frame : VisionFrame, frame_number : int) -> VisionFrame:
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
