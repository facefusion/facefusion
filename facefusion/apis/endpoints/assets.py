import tempfile
from typing import Union

from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from facefusion import session_manager, translator
from facefusion.apis import asset_store
from facefusion.apis.asset_helper import sanitize_filename, serialize_asset
from facefusion.apis.endpoints.session import extract_access_token
from facefusion.filesystem import get_file_extension, is_file, remove_file

MAX_SOURCE_FILES = 100
MAX_TARGET_FILES = 1


async def upload_assets(request : Request) -> JSONResponse:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)
	asset_type = request.query_params.get('type')
	error_message = None

	if asset_type in [ 'source', 'target' ]:
		max_files = MAX_SOURCE_FILES if asset_type == 'source' else MAX_TARGET_FILES
		form = await request.form(max_files = max_files, max_fields = 10)
		files = form.getlist('file')

		if files and isinstance(files[0], UploadFile):
			if len(files) == 1 if asset_type == 'target' else True:
				asset_ids = []

				for file in files:
					filename = sanitize_filename(file.filename) if file.filename else 'upload' #type:ignore[union-attr]
					file_extension = get_file_extension(filename)

					with tempfile.NamedTemporaryFile(suffix = file_extension, delete = False) as temp_file:
						content = await file.read() #type:ignore[union-attr]
						temp_file.write(content)
						file_path = temp_file.name

					asset = asset_store.create_asset(session_id, asset_type, file_path) #type:ignore[arg-type]

					if asset:
						asset_ids.append(asset.get('id'))
						continue

					if is_file(file_path):
						remove_file(file_path)

					error_message = 'unsupported_file_format'
					break

				if asset_ids and error_message is None:
					if asset_type == 'target':
						return JSONResponse(
						{
							'asset_id': asset_ids[0]
						}, status_code = HTTP_201_CREATED)

					return JSONResponse(
					{
						'asset_ids': asset_ids
					}, status_code = HTTP_201_CREATED)

			if error_message is None:
				error_message = 'single_file_expected'

		if error_message is None:
			error_message = 'invalid_file_object' if files else 'no_file_provided'

	if error_message is None:
		error_message = 'invalid_asset_type'

	return JSONResponse(
	{
		'message': translator.get(error_message, 'facefusion.apis')
	}, status_code = HTTP_400_BAD_REQUEST)


async def list_assets(request : Request) -> JSONResponse:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)
	asset_type = request.query_params.get('type')
	media = request.query_params.get('media')

	if asset_type and asset_type not in [ 'source', 'target' ]:
		return JSONResponse(
		{
			'message': translator.get('invalid_asset_type', 'facefusion.apis')
		}, status_code = HTTP_400_BAD_REQUEST)

	if media and media not in [ 'image', 'video', 'audio' ]:
		return JSONResponse(
		{
			'message': translator.get('invalid_media_type', 'facefusion.apis')
		}, status_code = HTTP_400_BAD_REQUEST)

	assets = asset_store.list_assets(
		session_id, #type:ignore[arg-type]
		asset_type, #type:ignore[arg-type]
		media #type:ignore[arg-type]
	)
	serialized_assets = [ serialize_asset(asset) for asset in assets ] #type:ignore[arg-type]

	return JSONResponse(
	{
		'assets': serialized_assets,
		'count': len(serialized_assets)
	}, status_code = HTTP_200_OK)


async def get_asset(request : Request) -> Union[JSONResponse, FileResponse]:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)
	asset_id = request.path_params.get('asset_id')
	action = request.query_params.get('action')
	asset = asset_store.get_asset(session_id, asset_id) #type:ignore[arg-type]

	if asset:
		if action == 'download':
			file_path = asset.get('path')

			if file_path and is_file(file_path):
				return FileResponse(file_path, filename = asset.get('name')) #type:ignore[arg-type]

		return JSONResponse(serialize_asset(asset), status_code = HTTP_200_OK) #type:ignore[arg-type]

	return JSONResponse(
	{
		'message': translator.get('asset_not_found', 'facefusion.apis')
	}, status_code = HTTP_404_NOT_FOUND)


async def delete_asset(request : Request) -> JSONResponse:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)
	asset_id = request.path_params.get('asset_id')

	if asset_store.delete_asset(session_id, asset_id): #type:ignore[arg-type]
		return JSONResponse(
		{
			'message': translator.get('asset_deleted', 'facefusion.apis')
		}, status_code = HTTP_200_OK)

	return JSONResponse(
	{
		'message': translator.get('asset_not_found', 'facefusion.apis')
	}, status_code = HTTP_404_NOT_FOUND)
