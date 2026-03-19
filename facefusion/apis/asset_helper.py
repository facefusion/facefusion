import asyncio
import os
import queue
import uuid
from functools import partial
from typing import List, Optional

from starlette.datastructures import UploadFile

import facefusion.choices
from facefusion import ffmpeg, process_manager, state_manager
from facefusion.audio import detect_audio_duration
from facefusion.ffprobe import detect_audio_channel_total, detect_audio_frame_total, detect_audio_sample_rate
from facefusion.filesystem import create_directory, get_file_extension, get_file_format, is_audio, is_image, is_video
from facefusion.types import AudioMetadata, ChunkQueue, ImageMetadata, MediaType, VideoMetadata
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


async def feed_chunk_queue(upload_file : UploadFile, chunk_queue : ChunkQueue) -> None:
	while chunk := await upload_file.read(1024):
		chunk_queue.put(chunk)
	chunk_queue.put(None)


def read_chunk_queue(chunk_queue : ChunkQueue) -> Optional[bytes]:
	return chunk_queue.get()


async def save_asset_files(upload_files : List[UploadFile]) -> List[str]:
	asset_paths : List[str] = []
	security_strategy = state_manager.get_item('api_security_strategy') or 'strict'

	for upload_file in upload_files:
		file_format = get_file_format(upload_file.filename)
		file_extension = get_file_extension(upload_file.filename)
		media_type = detect_media_type_by_format(file_format)
		temp_path = state_manager.get_temp_path()

		create_directory(temp_path)

		asset_file_name = uuid.uuid4().hex
		asset_path = os.path.join(temp_path, asset_file_name + file_extension)
		chunk_queue : ChunkQueue = queue.SimpleQueue()

		process_manager.start()

		feed_task = asyncio.create_task(feed_chunk_queue(upload_file, chunk_queue))
		sanitize_result = await asyncio.to_thread(ffmpeg.sanitize_media, media_type, file_format, partial(read_chunk_queue, chunk_queue), asset_path, security_strategy)
		await feed_task

		if sanitize_result:
			asset_paths.append(asset_path)

		process_manager.end()

	return asset_paths
