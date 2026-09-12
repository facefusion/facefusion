import uuid
from datetime import datetime, timedelta
from typing import Optional, cast

from facefusion import store_creator
from facefusion.apis.asset_helper import detect_media_type_by_path, extract_image_metadata
from facefusion.ffprobe import extract_audio_metadata, extract_video_metadata
from facefusion.filesystem import get_file_format, get_file_name, get_file_size
from facefusion.session_manager import resolve_owner_id
from facefusion.types import AssetId, AssetSet, AssetType, AudioAsset, AudioFormat, ImageAsset, ImageFormat, Store, VideoAsset, VideoFormat

ASSET_STORE : Store = store_creator.create_store({})


def init() -> None:
	owner_id = resolve_owner_id()
	store_creator.init_content(ASSET_STORE, owner_id)


def create_asset(asset_type : AssetType, asset_path : str) -> Optional[AudioAsset | ImageAsset | VideoAsset]:
	asset_id = str(uuid.uuid4())
	asset_name = get_file_name(asset_path)
	asset_format = get_file_format(asset_path)
	asset_size = get_file_size(asset_path)
	media_type = detect_media_type_by_path(asset_path)
	created_at = datetime.now()
	expires_at = created_at + timedelta(hours = 2)
	asset_set = get_assets()

	if media_type == 'audio':
		asset_set[asset_id] = cast(AudioAsset,
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
		asset_set[asset_id] = cast(ImageAsset,
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
		asset_set[asset_id] = cast(VideoAsset,
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

	return asset_set.get(asset_id)


def get_assets() -> AssetSet:
	owner_id = resolve_owner_id()

	return store_creator.get_content(ASSET_STORE, owner_id)


def get_asset(asset_id : AssetId) -> Optional[AudioAsset | ImageAsset | VideoAsset]:
	return get_assets().get(asset_id)


def delete_asset(asset_id : AssetId) -> None:
	asset_set = get_assets()

	if asset_id in asset_set:
		del asset_set[asset_id]


def delete_assets() -> None:
	owner_id = resolve_owner_id()
	store_creator.init_content(ASSET_STORE, owner_id)
