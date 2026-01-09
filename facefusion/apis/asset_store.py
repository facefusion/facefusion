import uuid
from typing import Dict, Optional

ASSET_STORE : Dict[str, Dict[str, str]] = {}


def get_asset(asset_id : str) -> Optional[Dict[str, str]]:
	return ASSET_STORE.get(asset_id)


def register_asset(path : str) -> str:
	asset_id = str(uuid.uuid4())

	ASSET_STORE[asset_id] =\
	{
		'id': asset_id,
		'path': path
	}
	return asset_id


def clear() -> None:
	ASSET_STORE.clear()
