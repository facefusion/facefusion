import os
import tempfile
from typing import List, Optional

from starlette.datastructures import UploadFile

import facefusion.choices
from facefusion import ffmpeg, process_manager, state_manager
from facefusion.audio import detect_audio_duration
from facefusion.ffprobe import detect_audio_channel_total, detect_audio_frame_total, detect_audio_sample_rate
from facefusion.filesystem import create_directory, get_file_extension, get_file_format, get_file_name, is_audio, is_image, is_video, remove_file
from facefusion.types import AudioMetadata, ImageMetadata, MediaType, VideoMetadata
from facefusion.vision import count_video_frame_total, detect_image_resolution, detect_video_duration, detect_video_fps, detect_video_resolution


def extract_audio_metadata(file_path : str) -> AudioMetadata:
	metadata : AudioMetadata =\
	{
		'duration': detect_audio_duration(file_path),
		'frame_total': detect_audio_frame_total(file_path),
		'sample_rate': detect_audio_sample_rate(file_path),
		'channels': detect_audio_channel_total(file_path)
	}
	return metadata


def extract_image_metadata(file_path : str) -> ImageMetadata:
	metadata : ImageMetadata =\
	{
		'resolution': detect_image_resolution(file_path)
	}
	return metadata


def extract_video_metadata(file_path : str) -> VideoMetadata:
	metadata : VideoMetadata =\
	{
		'duration': detect_video_duration(file_path),
		'frame_total': count_video_frame_total(file_path),
		'fps': detect_video_fps(file_path),
		'resolution': detect_video_resolution(file_path)
	}
	return metadata


def detect_media_type_by_path(file_path : str) -> Optional[MediaType]:
	if is_audio(file_path):
		return 'audio'
	if is_image(file_path):
		return 'image'
	if is_video(file_path):
		return 'video'
	return None


def detect_media_type_by_format(file_format : str) -> Optional[MediaType]:
	if file_format in facefusion.choices.audio_set:
		return 'audio'
	if file_format in facefusion.choices.image_set:
		return 'image'
	if file_format in facefusion.choices.video_set:
		return 'video'
	return None


def validate_asset_files(upload_files : List[UploadFile]) -> bool:
	available_encoder_set = ffmpeg.get_available_encoder_set()

	for upload_file in upload_files:
		file_format = get_file_format(upload_file.filename)
		media_type = detect_media_type_by_format(file_format)

		if media_type == 'audio' and facefusion.choices.audio_set.get(file_format) not in available_encoder_set.get('audio'): #type:ignore[call-overload]
			return False

		if media_type == 'image' and facefusion.choices.image_set.get(file_format) not in available_encoder_set.get('image'): #type:ignore[call-overload]
			return False

		if media_type == 'video' and facefusion.choices.video_set.get(file_format) not in available_encoder_set.get('video'): #type:ignore[call-overload]
			return False

	return True


async def save_asset_files(upload_files : List[UploadFile]) -> List[str]:
	asset_paths : List[str] = []

	for upload_file in upload_files:
		upload_file_extension = get_file_extension(upload_file.filename)

		with tempfile.NamedTemporaryFile(suffix = upload_file_extension, delete = False) as temp_file:

			while upload_chunk := await upload_file.read(1024):
				temp_file.write(upload_chunk)

			temp_file.flush()

			media_type = detect_media_type_by_path(temp_file.name)
			temp_path = state_manager.get_temp_path()

			create_directory(temp_path)

			asset_file_name = get_file_name(temp_file.name)
			asset_path = os.path.join(temp_path, asset_file_name + upload_file_extension)

			process_manager.start()

			if media_type == 'audio' and ffmpeg.sanitize_audio(temp_file.name, asset_path):
				asset_paths.append(asset_path)

			if media_type == 'image' and ffmpeg.sanitize_image(temp_file.name, asset_path):
				asset_paths.append(asset_path)

			if media_type == 'video' and ffmpeg.sanitize_video(temp_file.name, asset_path):
				asset_paths.append(asset_path)

			process_manager.end()

		remove_file(temp_file.name)

	return asset_paths
