from typing import List

from facefusion import logger, state_manager
from facefusion.audio import create_empty_audio_frame
from facefusion.face_selector import decode_face_selector_maps
from facefusion.filesystem import is_image, is_video
from facefusion.processors.core import get_processors_modules
from facefusion.types import VisionFrame
from facefusion.vision import extract_vision_mask, read_static_image, read_static_video_frame


def process_stream_frame(source_vision_frames : List[VisionFrame], target_vision_frame : VisionFrame) -> VisionFrame:
	source_audio_frame = create_empty_audio_frame()
	source_voice_frame = create_empty_audio_frame()
	temp_vision_frame = target_vision_frame.copy()
	temp_vision_mask = extract_vision_mask(temp_vision_frame)
	reference_vision_frames = get_reference_vision_frames()

	for processor_module in get_processors_modules(state_manager.get_item('processors')):
		logger.disable()

		if processor_module.pre_process('stream'):
			logger.enable()
			temp_vision_frame, temp_vision_mask = processor_module.process_frame(
			{
				'reference_vision_frames': reference_vision_frames,
				'source_vision_frames': source_vision_frames,
				'source_audio_frame': source_audio_frame,
				'source_voice_frame': source_voice_frame,
				'target_vision_frames': [ target_vision_frame ],
				'temp_vision_frame': temp_vision_frame,
				'temp_vision_mask': temp_vision_mask
			})

		logger.enable()

	return temp_vision_frame


def get_reference_vision_frames() -> List[VisionFrame]:
	reference_vision_frames = []
	target_path = state_manager.get_item('target_path')
	face_selector_mode = state_manager.get_item('face_selector_mode')
	face_selector_maps = decode_face_selector_maps(state_manager.get_item('face_selector_maps'))

	if face_selector_mode == 'reference':
		for face_selector_map in face_selector_maps:
			for reference_face in face_selector_map.get('reference_faces'):
				if is_video(target_path):
					reference_vision_frames.append(read_static_video_frame(target_path, reference_face.get('frame_index')))
				if is_image(target_path):
					reference_vision_frames.append(read_static_image(target_path))

	return reference_vision_frames
