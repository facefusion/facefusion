from typing import Optional

from starlette.datastructures import Headers
from starlette.types import Scope

from facefusion.audio import detect_audio_duration
from facefusion.types import AudioMetadata, ImageMetadata, VideoMetadata
from facefusion.vision import count_video_frame_total, detect_image_resolution, detect_video_duration, detect_video_fps, detect_video_resolution


def get_sec_websocket_protocol(scope : Scope) -> Optional[str]:
	protocol_header = Headers(scope = scope).get('Sec-WebSocket-Protocol')

	if protocol_header:
		protocol, _, _ = protocol_header.partition(',')
		return protocol.strip()

	return None


def extract_audio_metadata(file_path : str) -> AudioMetadata:
	metadata : AudioMetadata =\
	{
		'duration' : detect_audio_duration(file_path)
	}
	return metadata


def extract_image_metadata(file_path : str) -> ImageMetadata:
	metadata : ImageMetadata =\
	{
		'resolution' : detect_image_resolution(file_path)
	}
	return metadata


def extract_video_metadata(file_path : str) -> VideoMetadata:
	metadata : VideoMetadata =\
	{
		'duration' : detect_video_duration(file_path),
		'frame_total' : count_video_frame_total(file_path),
		'fps' : detect_video_fps(file_path),
		'resolution' : detect_video_resolution(file_path)
	}
	return metadata
