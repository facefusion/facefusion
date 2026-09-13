import os
from typing import List

from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_415_UNSUPPORTED_MEDIA_TYPE

from facefusion import translator
from facefusion.apis import asset_store
from facefusion.apis.asset_helper import capture_asset_faces, capture_asset_frames, save_asset_files, validate_asset_files, validate_frame_resolution, validate_file_size
from facefusion.filesystem import remove_file
from facefusion.vision import is_vision_frames, to_strip_buffer


async def get_assets(request : Request) -> Response:
	asset_set = asset_store.get_assets()
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


async def get_asset(request : Request) -> Response:
	asset_id = request.path_params.get('asset_id')
	asset = asset_store.get_asset(asset_id)

	if asset:
		if asset.get('media') in [ 'image', 'video' ] and request.query_params.get('action') == 'capture':
			resolution = request.query_params.get('resolution')
			frame_indexes = request.query_params.getlist('frame_index')
			vision_frames = []

			if validate_frame_resolution(resolution):

				if request.query_params.get('subject') == 'frame':
					vision_frames = capture_asset_frames(asset, frame_indexes, resolution) #type:ignore[arg-type]

				if request.query_params.get('subject') == 'face':
					vision_frames = capture_asset_faces(asset, frame_indexes, resolution) #type:ignore[arg-type]

			if is_vision_frames(vision_frames):
				return Response(content = to_strip_buffer(vision_frames), media_type = 'image/jpeg')

			return Response(status_code = HTTP_400_BAD_REQUEST)

		if request.query_params.get('action') == 'download':
			asset_path = asset.get('path')

			if os.path.exists(asset_path):
				return FileResponse(asset_path, filename = asset.get('name'))

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

	return JSONResponse(
	{
		'message': translator.get('something_went_wrong', 'facefusion.apis')
	}, status_code = HTTP_404_NOT_FOUND)


async def upload_assets(request : Request) -> Response:
	asset_type = request.query_params.get('type')

	if asset_type in [ 'source', 'target' ]:
		form = await request.form()
		upload_files = form.getlist('file')

		if upload_files and validate_file_size(upload_files) and validate_asset_files(upload_files):
			asset_paths = await save_asset_files(upload_files)

			if asset_paths:
				asset_ids : List[str] = []

				for asset_path in asset_paths:
					asset = asset_store.create_asset(asset_type, asset_path)

					if asset:
						asset_id = asset.get('id')

						if asset_id:
							asset_ids.append(asset_id)

				if asset_ids:
					return JSONResponse(
					{
						'asset_ids': asset_ids
					}, status_code = HTTP_201_CREATED)

			return Response(status_code = HTTP_415_UNSUPPORTED_MEDIA_TYPE)

	return Response(status_code = HTTP_400_BAD_REQUEST)


async def delete_assets(request : Request) -> Response:
	asset_set = asset_store.get_assets()
	asset_ids : List[str] = []

	if asset_set:
		for asset in asset_set.values():
			if remove_file(asset.get('path')):
				asset_ids.append(asset.get('id'))

		for asset_id in asset_ids:
			asset_store.delete_asset(asset_id)

	return Response(status_code = HTTP_200_OK)


async def delete_asset(request : Request) -> Response:
	asset_id = request.path_params.get('asset_id')
	asset = asset_store.get_asset(asset_id)

	if asset and remove_file(asset.get('path')):
		asset_store.delete_asset(asset_id)
		return Response(status_code = HTTP_200_OK)

	return Response(status_code = HTTP_404_NOT_FOUND)
