import tempfile
from typing import List, Tuple

from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from facefusion import session_manager
from facefusion.apis import asset_store
from facefusion.apis.endpoints.session import extract_access_token
from facefusion.filesystem import get_file_extension, is_audio, is_file, is_image, is_video, remove_file
from facefusion.types import MediaType


async def upload_asset(request : Request) -> JSONResponse:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)
	asset_type = request.query_params.get('type')

	if session_id and asset_type in [ 'source', 'target' ]:
		form = await request.form()
		files = [ file for file in form.getlist('file') if isinstance(file, UploadFile) ]

		if asset_type == 'target':
			files = files[:1]

		prepared_files = await prepare_files(files)

		if prepared_files:
			asset_ids : List[str] = []

			for file_path, media_type in prepared_files:
				asset = asset_store.create_asset(session_id, asset_type, media_type, file_path) #type:ignore[arg-type]

				if asset:
					asset_id = asset.get('id')

					if asset_id:
						asset_ids.append(asset_id)

			if asset_ids:
				if asset_type == 'target':
					return JSONResponse({ 'asset_id': asset_ids[0] }, status_code = HTTP_201_CREATED)

				return JSONResponse({ 'asset_ids': asset_ids }, status_code = HTTP_201_CREATED)

	return JSONResponse({}, status_code = HTTP_400_BAD_REQUEST)


async def prepare_files(files : List[UploadFile]) -> List[Tuple[str, MediaType]]:
	prepared_files : List[Tuple[str, MediaType]] = []

	for file in files:
		file_extension = get_file_extension(file.filename)

		with tempfile.NamedTemporaryFile(suffix = file_extension, delete = False) as temp_file:
			content = await file.read()
			temp_file.write(content)
			file_path = temp_file.name

		media_type : MediaType | None = None

		if is_audio(file_path):
			media_type = 'audio'
		if is_image(file_path):
			media_type = 'image'
		if is_video(file_path):
			media_type = 'video'

		if media_type:
			prepared_files.append((file_path, media_type))

		if not media_type and is_file(file_path):
			remove_file(file_path)

	return prepared_files
