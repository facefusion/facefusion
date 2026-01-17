import tempfile
from typing import List

from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from facefusion import session_manager
from facefusion.apis import asset_store
from facefusion.apis.asset_helper import detect_media_type
from facefusion.apis.endpoints.session import extract_access_token
from facefusion.filesystem import get_file_extension, is_file, remove_file


async def upload_asset(request : Request) -> JSONResponse:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)
	asset_type = request.query_params.get('type')

	if session_id and asset_type in [ 'source', 'target' ]:
		form = await request.form()
		files = [ file for file in form.getlist('file') if isinstance(file, UploadFile) ]

		if asset_type == 'target':
			files = files[:1]

		media_files = await prepare_media_files(files)

		if media_files:
			asset_ids : List[str] = []

			for media_file in media_files:
				media_type = detect_media_type(media_file)

				if media_type:
					asset = asset_store.create_asset(session_id, asset_type, media_type, media_file) #type:ignore[arg-type]

					if asset:
						asset_id = asset.get('id')

						if asset_id:
							asset_ids.append(asset_id)

			if asset_ids:
				if asset_type == 'target':
					return JSONResponse({ 'asset_id': asset_ids[0] }, status_code = HTTP_201_CREATED)

				return JSONResponse({ 'asset_ids': asset_ids }, status_code = HTTP_201_CREATED)

	return JSONResponse({}, status_code = HTTP_400_BAD_REQUEST)


async def prepare_media_files(files : List[UploadFile]) -> List[str]:
	media_files : List[str] = []

	for file in files:
		file_extension = get_file_extension(file.filename)

		with tempfile.NamedTemporaryFile(suffix = file_extension, delete = False) as temp_file:
			content = await file.read()
			temp_file.write(content)
			file_path = temp_file.name

		media_type = detect_media_type(file_path)

		if media_type:
			media_files.append(file_path)

		if not media_type and is_file(file_path):
			remove_file(file_path)

	return media_files
