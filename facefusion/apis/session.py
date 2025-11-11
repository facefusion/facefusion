import os
import secrets
import time
from typing import Dict
from typing import TypeAlias

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.status import HTTP_200_OK
from starlette.status import HTTP_201_CREATED
from starlette.status import HTTP_204_NO_CONTENT
from starlette.status import HTTP_401_UNAUTHORIZED

from facefusion import logger
from facefusion import session_manager
from facefusion import translator
from facefusion.apis.session_middleware import get_valid_bearer_token


JSON : TypeAlias = Dict[str, object]


def error_response(message : str) -> Response:
	return JSONResponse({ "error": { "code": "UNAUTHORIZED", "message": message, "details": {} } }, status_code = HTTP_401_UNAUTHORIZED)


async def create_session(request : Request) -> Response:
	body = await request.json()

	env_api_key = os.getenv('FACEFUSION_API_KEY')
	request_api_key = body.get('api_key')

	if request_api_key and not env_api_key:
		message = translator.get('errors.invalid_api_key', __package__) or 'Invalid API key'
		return error_response(message)

	if env_api_key and request_api_key != env_api_key:
		message = translator.get('errors.invalid_api_key', __package__) or 'Invalid API key'
		return error_response(message)
	token = secrets.token_urlsafe(32)
	refresh_token = secrets.token_urlsafe(32)
	expires_at = int(time.time()) + 3600
	session_data : JSON =\
	{
		"token": token,
		"refresh_token": refresh_token,
		"created_at": int(time.time()),
		"expires_at": expires_at
	}
	session_manager.set_session(token, session_data)
	session_manager.set_session(refresh_token, session_data)
	payload : JSON =\
	{
		"access_token": token,
		"refresh_token": refresh_token,
		"token_type": "Bearer",
		"expires_in": 3600,
		"expires_at": expires_at
	}
	logger.info('POST ' + str(request.url.path), __package__)
	return JSONResponse(payload, status_code = HTTP_201_CREATED)


async def get_session(request : Request) -> Response:
	token = get_valid_bearer_token(request.headers) or ''
	if not token:
		message = translator.get('errors.missing_auth', __package__) or 'Missing Authorization header'
		return error_response(message)
	session_data = session_manager.get_session(token)
	payload : JSON =\
	{
		"created_at": int(session_data.get('created_at')),
		"expires_at": int(session_data.get('expires_at')),
		"last_activity": int(time.time())
	}
	logger.info('GET ' + str(request.url.path), __package__)

	return JSONResponse(payload, status_code = HTTP_200_OK)


async def refresh_session(request : Request) -> Response:
	body = await request.json()
	old_refresh_token = str(body.get('refresh_token', ''))
	session_data = session_manager.get_session(old_refresh_token)
	if not session_data:
		message = translator.get('errors.invalid_refresh_token', __package__) or 'Invalid refresh token'
		return error_response(message)
	session_manager.clear_session(str(session_data.get('token')))
	session_manager.clear_session(old_refresh_token)
	new_token = secrets.token_urlsafe(32)
	new_refresh_token = secrets.token_urlsafe(32)
	expires_at = int(time.time()) + 3600
	new_session_data : JSON =\
	{
		"token": new_token,
		"refresh_token": new_refresh_token,
		"created_at": int(session_data.get('created_at')),
		"expires_at": expires_at
	}
	session_manager.set_session(new_token, new_session_data)
	session_manager.set_session(new_refresh_token, new_session_data)
	payload : JSON =\
	{
		"access_token": new_token,
		"refresh_token": new_refresh_token,
		"token_type": "Bearer",
		"expires_in": 3600,
		"expires_at": expires_at
	}
	logger.info('POST ' + str(request.url.path), __package__)
	return JSONResponse(payload, status_code = HTTP_200_OK)


async def destroy_session(request : Request) -> Response:
	token = get_valid_bearer_token(request.headers) or ''
	if not token:
		message = translator.get('errors.invalid_or_expired', __package__) or 'Invalid or expired token'
		return error_response(message)
	session_data = session_manager.get_session(token)
	if session_data:
		refresh_tok = str(session_data.get('refresh_token'))
		session_manager.clear_session(token)
		session_manager.clear_session(refresh_tok)
	logger.info('DELETE ' + str(request.url.path), __package__)
	return Response(status_code = HTTP_204_NO_CONTENT)
