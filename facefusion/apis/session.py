import os
import secrets
from datetime import datetime, timedelta

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_401_UNAUTHORIZED

from facefusion import session_manager
from facefusion.apis.session_middleware import extract_access_token
from facefusion.types import Session


def build_session() -> Session:
	session : Session =\
	{
		'access_token': secrets.token_urlsafe(128),
		'refresh_token': secrets.token_urlsafe(128),
		'created_at': datetime.now(),
		'expires_at': datetime.now() + timedelta(seconds = 3600)
	}

	return session


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
