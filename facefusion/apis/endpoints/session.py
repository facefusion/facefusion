import secrets

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND

from facefusion import session_context, session_manager, state_manager, translator
from facefusion.apis import asset_store
from facefusion.apis.session_helper import extract_access_token, validate_api_key
from facefusion.filesystem import remove_directory


async def create_session(request : Request) -> JSONResponse:
	body = await request.json()

	if validate_api_key(body.get('api_key')):
		session_id = secrets.token_urlsafe(16)
		session = session_manager.create_session()
		session_context.set_session_id(session_id)
		session_manager.set_session(session_id, session)

		local_state = state_manager.get_context_state('cli', session_context.resolve_local_id())
		state_manager.set_state(session_id, local_state.copy())

		return JSONResponse(
		{
			'access_token': session.get('access_token'),
			'refresh_token': session.get('refresh_token')
		}, status_code = HTTP_201_CREATED)

	return JSONResponse(
	{
		'message': translator.get('something_went_wrong', 'facefusion.apis')
	}, status_code = HTTP_401_UNAUTHORIZED)


async def get_session(request : Request) -> JSONResponse:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)
	session = session_manager.get_session(session_id)

	return JSONResponse(
	{
		'access_token': session.get('access_token'),
		'refresh_token': session.get('refresh_token'),
		'created_at': session.get('created_at').isoformat(),
		'expires_at': session.get('expires_at').isoformat()
	}, status_code = HTTP_200_OK)


async def refresh_session(request : Request) -> JSONResponse:
	body = await request.json()

	for session_id, session in session_manager.SESSIONS.items():
		if session.get('refresh_token') == body.get('refresh_token') and session_manager.validate_session(session_id):
			__session__ = session_manager.create_session()
			session_manager.set_session(session_id, __session__)

			return JSONResponse(
			{
				'access_token': __session__.get('access_token'),
				'refresh_token': __session__.get('refresh_token')
			}, status_code = HTTP_200_OK)

	return JSONResponse(
	{
		'message': translator.get('something_went_wrong', 'facefusion.apis')
	}, status_code = HTTP_401_UNAUTHORIZED)


async def destroy_session(request : Request) -> JSONResponse:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)

	if session_id:
		session_context.set_session_id(session_id)

		if remove_directory(state_manager.resolve_temp_path()):
			asset_store.delete_assets(session_id)
			state_manager.clear_state(session_id)
			session_manager.clear_session(session_id)

			return JSONResponse(
			{
				'message': translator.get('ok', 'facefusion.apis')
			}, status_code = HTTP_200_OK)

		return JSONResponse(
		{
			'message': translator.get('something_went_wrong', 'facefusion.apis')
		}, status_code = HTTP_404_NOT_FOUND)

	return JSONResponse(
	{
		'message': translator.get('something_went_wrong', 'facefusion.apis')
	}, status_code = HTTP_401_UNAUTHORIZED)
