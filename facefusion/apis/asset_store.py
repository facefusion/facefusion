import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, cast

from facefusion.apis.asset_helper import detect_media_type, extract_audio_metadata, extract_image_metadata, extract_video_metadata
from facefusion.filesystem import get_file_format, get_file_name
from facefusion.types import AssetId, AssetStore, AssetType, AudioAsset, AudioFormat, ImageAsset, ImageFormat, SessionId, VideoAsset, VideoFormat

ASSET_STORE : AssetStore = {}


def create_asset(session_id : SessionId, asset_type : AssetType, asset_path : str) -> Optional[AudioAsset | ImageAsset | VideoAsset]:
	asset_id = str(uuid.uuid4())
	asset_name = get_file_name(asset_path)
	asset_format = get_file_format(asset_path)
	asset_size = os.path.getsize(asset_path)
	media_type = detect_media_type(asset_path)
	created_at = datetime.now()
	expires_at = created_at + timedelta(hours = 2)

	if session_id not in ASSET_STORE:
		ASSET_STORE[session_id] = {}

	if media_type == 'audio':
		ASSET_STORE[session_id][asset_id] = cast(AudioAsset,
		{
			'id': asset_id,
			'created_at': created_at,
			'expires_at': expires_at,
			'type': asset_type,
			'media': media_type,
			'name': asset_name,
			'format': cast(AudioFormat, asset_format),
			'size': asset_size,
			'path': asset_path,
			'metadata': extract_audio_metadata(asset_path)
		})

	if media_type == 'image':
		ASSET_STORE[session_id][asset_id] = cast(ImageAsset,
		{
			'id': asset_id,
			'created_at': created_at,
			'expires_at': expires_at,
			'type': asset_type,
			'media': media_type,
			'name': asset_name,
			'format': cast(ImageFormat, asset_format),
			'size': asset_size,
			'path': asset_path,
			'metadata': extract_image_metadata(asset_path)
		})

	if media_type == 'video':
		ASSET_STORE[session_id][asset_id] = cast(VideoAsset,
		{
			'id': asset_id,
			'created_at': created_at,
			'expires_at': expires_at,
			'type': asset_type,
			'media': media_type,
			'name': asset_name,
			'format': cast(VideoFormat, asset_format),
			'size': asset_size,
			'path': asset_path,
			'metadata': extract_video_metadata(asset_path)
		})

	return ASSET_STORE[session_id].get(asset_id)


def get_asset(session_id : SessionId, asset_id : AssetId) -> Optional[AudioAsset | ImageAsset | VideoAsset]:
	if session_id in ASSET_STORE:
		return ASSET_STORE[session_id].get(asset_id)
	return None


def clear() -> None:
	ASSET_STORE.clear()
