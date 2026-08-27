from typing import List

from facefusion import logger, state_manager
from facefusion.audio import create_empty_audio_frame
from facefusion.processors.core import get_processors_modules
from facefusion.types import VisionFrame
from facefusion.vision import extract_vision_mask


def process_stream_frame(source_vision_frames : List[VisionFrame], target_vision_frame : VisionFrame) -> VisionFrame:
	source_audio_frame = create_empty_audio_frame()
	source_voice_frame = create_empty_audio_frame()
	temp_vision_frame = target_vision_frame.copy()
	temp_vision_mask = extract_vision_mask(temp_vision_frame)

	for processor_module in get_processors_modules(state_manager.get_item('processors')):
		logger.disable()

		if processor_module.pre_process('stream'):
			logger.enable()
			temp_vision_frame, temp_vision_mask = processor_module.process_frame(
			{
				'source_vision_frames': source_vision_frames,
				'source_audio_frame': source_audio_frame,
				'source_voice_frame': source_voice_frame,
				'target_vision_frames': [ target_vision_frame ],
				'temp_vision_frame': temp_vision_frame,
				'temp_vision_mask': temp_vision_mask
			})
		logger.enable()

	return temp_vision_frame
