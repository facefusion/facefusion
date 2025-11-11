import os
import secrets
import time
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import TypeAlias

from starlette.authentication import AuthCredentials
from starlette.authentication import AuthenticationError
from starlette.authentication import SimpleUser
from starlette.requests import HTTPConnection
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.status import HTTP_200_OK
from starlette.status import HTTP_201_CREATED
from starlette.status import HTTP_204_NO_CONTENT
from starlette.status import HTTP_401_UNAUTHORIZED

from facefusion import logger
from facefusion import session_manager


JSON : TypeAlias = Dict[str, object]
AuthResult : TypeAlias = Optional[Tuple[AuthCredentials, SimpleUser]]

UNPROTECTED_PATHS = [ '/' ]


def error_response(message : str) -> Response:
	return JSONResponse({ "error": { "code": "UNAUTHORIZED", "message": message, "details": {} } }, status_code = HTTP_401_UNAUTHORIZED)


async def create_session(request : Request) -> Response:
	body = await request.json()
	api_key = os.getenv('FACEFUSION_API_KEY')
	request_api_key = str(body.get('api_key', ''))
	if request_api_key and not api_key:
		return error_response('Invalid API key')
	if api_key and request_api_key != api_key:
		return error_response('Invalid API key')
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


async def refresh_session(request : Request) -> Response:
	body = await request.json()
	old_refresh_token = str(body.get('refresh_token', ''))
	session_data = session_manager.get_session(old_refresh_token)
	if not session_data:
		return error_response('Invalid refresh token')
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
	token = str(request.scope.get('auth_token'))
	session_data = session_manager.get_session(token)
	if session_data:
		refresh_tok = str(session_data.get('refresh_token'))
		session_manager.clear_session(token)
		session_manager.clear_session(refresh_tok)
	logger.info('DELETE ' + str(request.url.path), __package__)
	return Response(status_code = HTTP_204_NO_CONTENT)


async def get_session(request : Request) -> Response:
	token = str(request.scope.get('auth_token'))
	session_data = session_manager.get_session(token)
	payload : JSON =\
	{
		"created_at": int(session_data.get('created_at')),
		"expires_at": int(session_data.get('expires_at')),
		"last_activity": int(time.time())
	}
	logger.info('GET ' + str(request.url.path), __package__)
	return JSONResponse(payload, status_code = HTTP_200_OK)


async def authenticate_bearer(conn : HTTPConnection) -> AuthResult:
	if conn.url.path in UNPROTECTED_PATHS or conn.scope.get('method') == 'OPTIONS':
		return None
	if conn.url.path == '/session' and conn.scope.get('method') in [ 'POST', 'PUT' ]:
		return None
	auth_header = conn.headers.get('Authorization', '')
	if not auth_header:
		raise AuthenticationError('Missing Authorization header')
	parts = auth_header.split(' ', 1)
	if len(parts) != 2 or parts[0].lower() != 'bearer':
		raise AuthenticationError('Invalid Authorization header format')
	token = parts[1]
	session_data = session_manager.get_session(token)
	if not session_data:
		raise AuthenticationError('Invalid or expired token')
	if int(time.time()) > int(session_data.get('expires_at')):
		session_manager.clear_session(token)
		session_manager.clear_session(str(session_data.get('refresh_token')))
		raise AuthenticationError('Token expired')
	return AuthCredentials([ 'authenticated' ]), SimpleUser(token)
