import uuid
from typing import Dict, Optional

_assets: Dict[str, Dict[str, str]] = {}


def register_asset(path: str, asset_id: Optional[str] = None) -> str:
	if asset_id is None:
		asset_id = str(uuid.uuid4())

	_assets[asset_id] = {
		'id': asset_id,
		'path': path
	}
	return asset_id


def get_asset(asset_id: str) -> Optional[Dict[str, str]]:
	return _assets.get(asset_id)


def clear() -> None:
	_assets.clear()

