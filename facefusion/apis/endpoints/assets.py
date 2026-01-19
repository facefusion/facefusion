import os
import tempfile
from typing import List

from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from facefusion import ffmpeg, process_manager, session_manager, state_manager
from facefusion.apis import asset_store
from facefusion.apis.asset_helper import detect_media_type
from facefusion.apis.endpoints.session import extract_access_token
from facefusion.filesystem import get_file_extension, remove_file


async def upload_asset(request : Request) -> Response:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)
	asset_type = request.query_params.get('type')

	if session_id and asset_type in [ 'source', 'target' ]:
		form = await request.form()
		upload_files = form.getlist('file')
		asset_paths = await save_asset_files(upload_files) # type: ignore[arg-type]

		if asset_paths:
			asset_ids : List[str] = []

			for asset_path in asset_paths:
				asset = asset_store.create_asset(session_id, asset_type, asset_path) # type: ignore[arg-type]
				asset_id = asset.get('id')

				if asset_id:
					asset_ids.append(asset_id)

			if asset_ids:
				return JSONResponse(
				{
					'asset_ids': asset_ids
				}, status_code = HTTP_201_CREATED)

	return Response(status_code = HTTP_400_BAD_REQUEST)


async def save_asset_files(upload_files : List[UploadFile]) -> List[str]:
	asset_paths : List[str] = []

	for upload_file in upload_files:
		upload_file_extension = get_file_extension(upload_file.filename)

		with tempfile.NamedTemporaryFile(suffix = upload_file_extension, delete = False) as temp_file:

			while upload_chunk := await upload_file.read(1024):
				temp_file.write(upload_chunk)

			temp_file.flush()

			media_type = detect_media_type(temp_file.name)
			temp_path = state_manager.get_temp_path()
			asset_path = os.path.join(temp_path, temp_file.name + '.' + upload_file_extension)

			process_manager.start()

			if media_type == 'audio' and ffmpeg.sanitize_audio(temp_file.name, asset_path):
				asset_paths.append(asset_path)

			if media_type == 'image' and ffmpeg.sanitize_image(temp_file.name, asset_path):
				asset_paths.append(asset_path)

			if media_type == 'video' and ffmpeg.sanitize_video(temp_file.name, asset_path):
				asset_paths.append(asset_path)

			process_manager.end()

		remove_file(temp_file.name)

	return asset_paths


async def get_assets(request : Request) -> Response:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)

	if session_id:
		asset_set = asset_store.get_assets(session_id)
		assets = []

		if asset_set:
			for asset in asset_set.values():
				assets.append(
				{
					'id': asset.get('id'),
					'created_at': asset.get('created_at').isoformat(),
					'expires_at': asset.get('expires_at').isoformat(),
					'type': asset.get('type'),
					'media': asset.get('media'),
					'name': asset.get('name'),
					'format': asset.get('format'),
					'size': asset.get('size'),
					'metadata': asset.get('metadata')
				})

		return JSONResponse(
		{
			'assets': assets
		}, status_code = HTTP_200_OK)

	return Response(status_code = HTTP_400_BAD_REQUEST)


async def get_asset(request : Request) -> Response:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)
	asset_id = request.path_params.get('asset_id')

	if session_id and asset_id:
		asset = asset_store.get_asset(session_id, asset_id)

		if asset:
			return JSONResponse(
			{
				'id': asset.get('id'),
				'created_at': asset.get('created_at').isoformat(),
				'expires_at': asset.get('expires_at').isoformat(),
				'type': asset.get('type'),
				'media': asset.get('media'),
				'name': asset.get('name'),
				'format': asset.get('format'),
				'size': asset.get('size'),
				'metadata': asset.get('metadata')
			}, status_code = HTTP_200_OK)

	return Response(status_code = HTTP_404_NOT_FOUND)


async def delete_assets(request : Request) -> Response:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)
	body = await request.json()
	asset_ids = body.get('asset_ids')

	if session_id and asset_ids:
		asset_set = asset_store.get_assets(session_id)

		if asset_set:
			for asset_id in asset_ids:
				if asset_id in asset_set:
					remove_file(asset_set.get(asset_id).get('path'))
			asset_store.delete_assets(session_id, asset_ids)
			return Response(status_code = HTTP_200_OK)

	return Response(status_code = HTTP_404_NOT_FOUND)
