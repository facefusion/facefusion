import secrets

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND

from facefusion import content_store, face_store, inference_manager, process_manager, rtc_store, session_context, session_manager, state_manager, store_creator, translator, video_manager
from facefusion.apis import asset_store
from facefusion.apis.session_helper import validate_api_key
from facefusion.apis.stream_manager import destroy_stream
from facefusion.filesystem import is_directory, remove_directory
from facefusion.jobs import job_manager


async def create_session(request : Request) -> JSONResponse:
	body = await request.json()

	if validate_api_key(body.get('api_key')):
		session_id = secrets.token_urlsafe(16)
		session = session_manager.create_api_session()
		session_context.set_session_id(session_id)
		session_manager.set_api_session(session_id, session)

		state_manager.init()
		asset_store.init()
		content_store.init()
		face_store.init()
		inference_manager.init()
		video_manager.init()
		process_manager.init()
		rtc_store.init()

		jobs_path = state_manager.get_jobs_path()
		job_manager.init_jobs(jobs_path)

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
	session_id = session_context.get_session_id()
	session = session_manager.get_api_session(session_id)

	return JSONResponse(
	{
		'access_token': session.get('access_token'),
		'refresh_token': session.get('refresh_token'),
		'created_at': session.get('created_at').isoformat(),
		'expires_at': session.get('expires_at').isoformat()
	}, status_code = HTTP_200_OK)


async def refresh_session(request : Request) -> JSONResponse:
	body = await request.json()

	for session_id, session in session_manager.API_SESSIONS.items():
		if session.get('refresh_token') == body.get('refresh_token') and session_manager.validate_api_session(session_id):
			__session__ = session_manager.create_api_session()
			session_manager.set_api_session(session_id, __session__)

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
	session_id = session_context.get_session_id()
	temp_path = state_manager.get_temp_path()
	jobs_path = state_manager.get_jobs_path()

	if is_directory(temp_path) and not remove_directory(temp_path):
		return JSONResponse(
		{
			'message': translator.get('directory_not_removed', 'facefusion.apis')
		}, status_code = HTTP_404_NOT_FOUND)

	if is_directory(jobs_path) and not remove_directory(jobs_path):
		return JSONResponse(
		{
			'message': translator.get('directory_not_removed', 'facefusion.apis')
		}, status_code = HTTP_404_NOT_FOUND)

	destroy_stream()
	video_manager.clear()
	session_manager.clear_api_session(session_id)

	stores =\
	[
		state_manager.STATE_SET,
		asset_store.ASSET_STORE,
		content_store.CONTENT_STORE,
		face_store.FACE_STORE,
		inference_manager.INFERENCE_POOL_STORE,
		process_manager.PROCESS_STORE,
		rtc_store.RTC_STORE,
		video_manager.VIDEO_POOL_STORE
	]

	for store in stores:
		store_creator.delete_content(store, session_id)

	return JSONResponse(
	{
		'message': translator.get('ok', 'facefusion.apis')
	}, status_code = HTTP_200_OK)
