import os
import re
from typing import Any, Dict, Optional

from facefusion.audio import detect_audio_duration
from facefusion.ffprobe import detect_audio_channel_total, detect_audio_format, detect_audio_frame_total, detect_audio_sample_rate
from facefusion.filesystem import is_audio, is_image, is_video
from facefusion.types import AudioMetadata, ImageMetadata, MediaType, VideoMetadata
from facefusion.vision import count_video_frame_total, detect_image_resolution, detect_video_duration, detect_video_fps, detect_video_resolution


def extract_audio_metadata(file_path : str) -> AudioMetadata:
	metadata : AudioMetadata =\
	{
		'duration' : detect_audio_duration(file_path),
		'sample_rate' : detect_audio_sample_rate(file_path),
		'frame_total' : detect_audio_frame_total(file_path),
		'channels' : detect_audio_channel_total(file_path),
		'format' : detect_audio_format(file_path)
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


def detect_media_type(file_path : str) -> Optional[MediaType]:
	if is_audio(file_path):
		return 'audio'
	if is_image(file_path):
		return 'image'
	if is_video(file_path):
		return 'video'
	return None


def sanitize_filename(filename : str) -> str:
	filename = os.path.basename(filename)
	filename = re.sub(r'[^\w\-.]', '_', filename)
	return filename[:255]


def serialize_asset(asset : Dict[str, Any]) -> Dict[str, Any]:
	return\
	{
		'id': asset.get('id'),
		'created_at': asset.get('created_at').isoformat(),
		'expires_at': asset.get('expires_at').isoformat(),
		'type': asset.get('type'),
		'media': asset.get('media'),
		'name': asset.get('name'),
		'format': asset.get('format'),
		'size': asset.get('size'),
		'metadata': asset.get('metadata')
	}
