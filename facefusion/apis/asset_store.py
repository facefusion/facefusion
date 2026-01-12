import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, cast

from facefusion.apis.api_helper import extract_audio_metadata, extract_image_metadata, extract_video_metadata
from facefusion.filesystem import get_file_format, get_file_name, is_audio, is_image, is_video
from facefusion.types import Asset, AssetId, AssetStore, AssetType, AudioFormat, ImageFormat, MediaType, SessionId, VideoFormat

ASSET_STORE : AssetStore = {}


def get_asset(session_id : SessionId, asset_id : AssetId) -> Optional[Asset]:
	if session_id in ASSET_STORE:
		return ASSET_STORE[session_id].get(asset_id)
	return None


def create_asset(session_id : SessionId, asset_type : AssetType, file_path : str) -> Optional[Asset]:
	asset_id = str(uuid.uuid4())
	media_type = detect_media_type(file_path)

	if media_type:
		file_name = get_file_name(file_path)
		file_format = get_file_format(file_path)
		file_size = os.path.getsize(file_path)
		created_at = datetime.now()
		expires_at = created_at + timedelta(hours = 24)
		asset =\
		{
			'id': asset_id,
			'created_at': created_at,
			'expires_at': expires_at,
			'type': asset_type,
			'name': file_name,
			'size': file_size,
			'path': file_path
		}

		if media_type == 'audio':
			asset.update(
			{
				'media': 'audio',
				'format': cast(AudioFormat, file_format),
				'metadata': extract_audio_metadata(file_path)
			})
		if media_type == 'image':
			asset.update(
			{
				'media': 'image',
				'format': cast(ImageFormat, file_format),
				'metadata': extract_image_metadata(file_path)
			})
		if media_type == 'video':
			asset.update(
			{
				'media': 'video',
				'format': cast(VideoFormat, file_format),
				'metadata': extract_video_metadata(file_path)
			})

		if session_id not in ASSET_STORE:
			ASSET_STORE[session_id] = {}

		ASSET_STORE[session_id][asset_id] = asset #type:ignore[assignment]
		return asset #type:ignore[return-value]

	return None


def clear() -> None:
	ASSET_STORE.clear()


def detect_media_type(file_path : str) -> Optional[MediaType]:
	if is_image(file_path):
		return 'image'
	if is_video(file_path):
		return 'video'
	if is_audio(file_path):
		return 'audio'
	return None
