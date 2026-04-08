import asyncio
import os
import uuid
from typing import List, Optional

from starlette.datastructures import UploadFile

import facefusion.choices
from facefusion import ffmpeg, process_manager, state_manager
from facefusion.filesystem import create_directory, get_file_extension, get_file_format, is_audio, is_image, is_video
from facefusion.types import ImageMetadata, MediaType
from facefusion.vision import detect_image_resolution


def extract_image_metadata(file_path : str) -> ImageMetadata:
	metadata : ImageMetadata =\
	{
		'resolution': detect_image_resolution(file_path)
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
	available_encoder_set = ffmpeg.get_static_available_encoder_set()

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
	api_security_strategy = state_manager.get_item('api_security_strategy')

	for upload_file in upload_files:
		file_format = get_file_format(upload_file.filename)
		file_extension = get_file_extension(upload_file.filename)
		media_type = detect_media_type_by_format(file_format)
		temp_path = state_manager.get_temp_path()

		create_directory(temp_path)

		asset_file_name = uuid.uuid4().hex
		asset_path = os.path.join(temp_path, asset_file_name + file_extension)
		file_content = await upload_file.read()

		process_manager.start()

		if media_type == 'audio' and await asyncio.to_thread(ffmpeg.sanitize_audio, file_content, asset_path, api_security_strategy):
			asset_paths.append(asset_path)

		if media_type == 'image' and await asyncio.to_thread(ffmpeg.sanitize_image, file_content, asset_path):
			asset_paths.append(asset_path)

		if media_type == 'video' and await asyncio.to_thread(ffmpeg.sanitize_video, file_content, asset_path, api_security_strategy):
			asset_paths.append(asset_path)

		process_manager.end()

	return asset_paths
