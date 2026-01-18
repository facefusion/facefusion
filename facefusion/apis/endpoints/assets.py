import os
import tempfile
from typing import List

from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from facefusion import ffmpeg, session_manager, state_manager
from facefusion.apis import asset_store
from facefusion.apis.asset_helper import detect_media_type
from facefusion.apis.endpoints.session import extract_access_token
from facefusion.filesystem import get_file_extension


async def upload_asset(request : Request) -> Response:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)
	asset_type = request.query_params.get('type')

	if session_id and asset_type in [ 'source', 'target' ]:
		form = await request.form()
		upload_files = form.getlist('file')
		asset_paths = await save_asset_files(upload_files)

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

		with tempfile.NamedTemporaryFile(suffix = upload_file_extension) as temp_file:

			while upload_chunk := await upload_file.read(1024):
				temp_file.write(upload_chunk)

			media_type = detect_media_type(temp_file.name)
			temp_path = state_manager.get_temp_path()
			asset_path = os.path.join(temp_path, temp_file.name + '.' + upload_file_extension)

			if media_type == 'audio' and ffmpeg.sanitize_audio(temp_file.name, asset_path):
				asset_paths.append(asset_path)

			if media_type == 'image' and ffmpeg.sanitize_image(temp_file.name, asset_path):
				asset_paths.append(asset_path)

			if media_type == 'video' and ffmpeg.sanitize_video(temp_file.name, asset_path):
				asset_paths.append(asset_path)

	return asset_paths
