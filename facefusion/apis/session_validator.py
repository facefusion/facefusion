import os
import secrets
from typing import Optional


def validate_api_key(api_key : Optional[str]) -> bool:
	__api_key__ = os.getenv('FACEFUSION_API_KEY')

	if api_key and __api_key__:
		return secrets.compare_digest(api_key, __api_key__)

	return bool(api_key) == bool(__api_key__)
