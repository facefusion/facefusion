import os
import secrets
import time

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.status import HTTP_200_OK
from starlette.status import HTTP_201_CREATED
from starlette.status import HTTP_204_NO_CONTENT
from starlette.status import HTTP_401_UNAUTHORIZED

# from facefusion import logger
from facefusion import session_manager, translator
# from facefusion import translator
from facefusion.apis.session_middleware import extract_access_token


async def create_session(request : Request) -> Response:
	body = await request.json()
	# env_api_key = os.getenv('FACEFUSION_API_KEY')
	request_api_key = body.get('api_key')

	# Reject if request has API key but env doesn't, or if they don't match
	if request_api_key and not os.getenv('FACEFUSION_API_KEY'):
		# message = translator.get('errors.invalid_api_key', __package__) or 'Invalid API key'
		# message = 'Invalid API key'
		return JSONResponse({ "error": { "message": "Invalid API key" } }, status_code = HTTP_401_UNAUTHORIZED)
	if os.getenv('FACEFUSION_API_KEY') and request_api_key != os.getenv('FACEFUSION_API_KEY'):
		# message = translator.get('errors.invalid_api_key', __package__) or 'Invalid API key'
		# message = 'Invalid API key'
		return JSONResponse(
		{
			"error":
			{
				"message": "Invalid API key"
			}
		}, status_code = HTTP_401_UNAUTHORIZED)

	# Create session
	token = secrets.token_urlsafe(32)
	refresh_token = secrets.token_urlsafe(32)
	# expires_at = int(time.time()) + 3600
	session_data = {"access_token": token, "refresh_token": refresh_token, "created_at": int(time.time()), "expires_at": int(time.time()) + 3600}
	session_manager.set_session(token, session_data)
	# payload : JSON =\
	# {
	# 	"access_token": token,
	# 	"refresh_token": refresh_token
	# 	# "token_type": "Bearer",
	# 	# "expires_in": 3600,
	# 	# "expires_at": int(time.time()) + 3600  # expires_at
	# }
	# logger.info('POST ' + str(request.url.path), __package__)
	return JSONResponse({"access_token": token, "refresh_token": refresh_token}, status_code = HTTP_201_CREATED)


async def get_session(request : Request) -> Response:
	access_token = extract_access_token(request.headers)

	if access_token and session_manager.get_session(access_token):
		return JSONResponse(session_manager.get_session(access_token), status_code = HTTP_200_OK)

	return Response(status_code = HTTP_401_UNAUTHORIZED)


async def refresh_session(request : Request) -> Response:
	body = await request.json()
	old_refresh_token = str(body.get('refresh_token', ''))
	old_access_token = None
	old_session_data = None
	for access_token, session_data in session_manager.SESSIONS.items():
		if session_data.get('refresh_token') == old_refresh_token:
			old_access_token = access_token
			old_session_data = session_data
			break
	if old_session_data and old_access_token:
		session_manager.clear_session(old_access_token)
		new_token = secrets.token_urlsafe(32)
		new_refresh_token = secrets.token_urlsafe(32)
		# expires_at = int(time.time()) + 3600
		new_session_data = {"access_token": new_token, "refresh_token": new_refresh_token, "created_at": int(time.time()), "expires_at": int(time.time()) + 3600}
		session_manager.set_session(new_token, new_session_data)
		# payload : JSON =\
		# {
		# 	"access_token": new_token,
		# 	"refresh_token": new_refresh_token
		# 	# "token_type": "Bearer",
		# 	# "expires_in": 3600,
		# 	# "expires_at": int(time.time()) + 3600  # expires_at
		# }
		# logger.info('POST ' + str(request.url.path), __package__)
		return JSONResponse({"access_token": new_token, "refresh_token": new_refresh_token}, status_code = HTTP_200_OK)

	# message = translator.get('errors.invalid_refresh_token', __package__) or 'Invalid refresh token'
	# message = 'Invalid refresh token'
	return JSONResponse({ "error": { "message": "Invalid refresh token" } }, status_code = HTTP_401_UNAUTHORIZED)


async def destroy_session(request : Request) -> Response:
	access_token = extract_access_token(request.headers)

	if access_token and session_manager.get_session(access_token):
		session_manager.clear_session(access_token)
		return Response(status_code = HTTP_204_NO_CONTENT)

	return Response(status_code = HTTP_401_UNAUTHORIZED)
