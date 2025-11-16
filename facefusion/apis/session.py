import os
from typing import Optional

from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED, HTTP_426_UPGRADE_REQUIRED
from starlette.types import ASGIApp, Receive, Scope, Send

from facefusion import session_manager, translator
from facefusion.types import Token


async def create_session(request : Request) -> JSONResponse:
	body = await request.json()

	if not body.get('api_key') or body.get('api_key') == os.getenv('FACEFUSION_API_KEY'):
		session = session_manager.create_session()
		session_manager.set_session(session.get('access_token'), session)

		return JSONResponse(
		{
			'access_token': session.get('access_token'),
			'refresh_token': session.get('refresh_token')
		}, status_code = HTTP_201_CREATED)

	return JSONResponse(
	{
		'message': translator.get('something_went_wrong', __package__)
	}, status_code = HTTP_401_UNAUTHORIZED)


async def get_session(request : Request) -> JSONResponse:
	access_token = extract_access_token(request.headers)

	if access_token:
		session = session_manager.get_session(access_token)

		if session:
			return JSONResponse(
			{
				'access_token': session.get('access_token'),
				'refresh_token': session.get('refresh_token'),
				'created_at': session.get('created_at').isoformat(),
				'expires_at': session.get('expires_at').isoformat()
			}, status_code = HTTP_200_OK)

	return JSONResponse(
	{
		'message': translator.get('something_went_wrong', __package__)
	}, status_code = HTTP_401_UNAUTHORIZED)


async def refresh_session(request : Request) -> JSONResponse:
	body = await request.json()

	for access_token, session in session_manager.SESSIONS.items():
		if session.get('refresh_token') == body.get('refresh_token'):
			session_manager.clear_session(access_token)
			session = session_manager.create_session()
			session_manager.set_session(session.get('access_token'), session)

			return JSONResponse(
			{
				'access_token': session.get('access_token'),
				'refresh_token': session.get('refresh_token')
			}, status_code = HTTP_200_OK)

	return JSONResponse(
	{
		'message': translator.get('something_went_wrong', __package__)
	}, status_code = HTTP_401_UNAUTHORIZED)


async def destroy_session(request : Request) -> JSONResponse:
	access_token = extract_access_token(request.headers)

	if access_token:
		session = session_manager.get_session(access_token)

		if session:
			session_manager.clear_session(access_token)
			return JSONResponse(
			{
				'message': translator.get('ok', __package__)
			}, status_code = HTTP_200_OK)

	return JSONResponse(
	{
		'message': translator.get('something_went_wrong', __package__)
	}, status_code = HTTP_401_UNAUTHORIZED)


def create_session_guard(app : ASGIApp) -> ASGIApp:
	async def middleware(scope : Scope, receive : Receive, send : Send) -> None:
		access_token = extract_access_token(Headers(scope = scope))

		if access_token and session_manager.validate_session(access_token):
			return await app(scope, receive, send)

		if access_token:
			session = session_manager.get_session(access_token)

			if session:
				response = JSONResponse(
				{
					'message': translator.get('invalid_access_token', __package__)
				}, status_code = HTTP_426_UPGRADE_REQUIRED)

				return await response(scope, receive, send)

		response = JSONResponse(
		{
			'message': translator.get('invalid_access_token', __package__)
		}, status_code = HTTP_401_UNAUTHORIZED)

		return await response(scope, receive, send)

	return middleware


def extract_access_token(headers : Headers) -> Optional[Token]:
	auth_header = headers.get('Authorization')

	if auth_header:
		auth_prefix, _, access_token = auth_header.partition(' ')

		if auth_prefix.lower() == 'bearer' and access_token:
			return access_token

	return None
