import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_401_UNAUTHORIZED, HTTP_426_UPGRADE_REQUIRED
from starlette.types import ASGIApp, Receive, Scope, Send

from facefusion import session_manager, translator
from facefusion.types import Session, Token


async def create_session(request : Request) -> Response:
	body = await request.json()

	if not body.get('api_key') or body.get('api_key') == os.getenv('FACEFUSION_API_KEY'):
		session = build_session()
		session_manager.set_session(session.get('access_token'), session)

		return JSONResponse(
		{
			'access_token': session.get('access_token'),
			'refresh_token': session.get('refresh_token')
		}, status_code = HTTP_201_CREATED)

	return Response(status_code = HTTP_401_UNAUTHORIZED)


async def get_session(request : Request) -> Response:
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

	return Response(status_code = HTTP_401_UNAUTHORIZED)


async def refresh_session(request : Request) -> Response:
	body = await request.json()

	for access_token, session in session_manager.SESSIONS.items():
		if session.get('refresh_token') == body.get('refresh_token'):
			session_manager.clear_session(access_token)
			session = build_session()
			session_manager.set_session(session.get('access_token'), session)

			return JSONResponse(
			{
				'access_token': session.get('access_token'),
				'refresh_token': session.get('refresh_token')
			}, status_code = HTTP_200_OK)

	return Response(status_code = HTTP_401_UNAUTHORIZED)


async def destroy_session(request : Request) -> Response:
	access_token = extract_access_token(request.headers)

	if access_token:
		session = session_manager.get_session(access_token)

		if session:
			session_manager.clear_session(access_token)
			return Response(status_code = HTTP_204_NO_CONTENT)

	return Response(status_code = HTTP_401_UNAUTHORIZED)


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
					'message': translator.get('errors.invalid_access_token', __package__)
				}, status_code = HTTP_426_UPGRADE_REQUIRED)

				return await response(scope, receive, send)

		response = JSONResponse(
		{
			'message': translator.get('errors.invalid_access_token', __package__)
		}, status_code = HTTP_401_UNAUTHORIZED)

		return await response(scope, receive, send)

	return middleware


def build_session() -> Session:
	session : Session =\
	{
		'access_token': secrets.token_urlsafe(128),
		'refresh_token': secrets.token_urlsafe(128),
		'created_at': datetime.now(),
		'expires_at': datetime.now() + timedelta(seconds = 3600)
	}

	return session


def extract_access_token(headers : Headers) -> Optional[Token]:
	auth_header = headers.get('Authorization')

	if auth_header:
		_, _, access_token = auth_header.partition(' ')

		if access_token:
			return access_token

	return None
