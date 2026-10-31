import os
import secrets
from datetime import datetime
from typing import Optional

from facefusion import session_manager
from facefusion.types import SessionId


def validate_api_key(api_key : Optional[str]) -> bool:
	__api_key__ = os.getenv('FACEFUSION_API_KEY')

	if api_key and __api_key__:
		return secrets.compare_digest(api_key, __api_key__)

	return bool(api_key) == bool(__api_key__)


def validate_access_token(session_id : SessionId) -> bool:
	api_session = session_manager.get_api_session(session_id)

	if api_session:
		created_at = api_session.get('created_at')
		expires_at = api_session.get('expires_at')

		return datetime.now() < created_at + (expires_at - created_at) / 2

	return False
