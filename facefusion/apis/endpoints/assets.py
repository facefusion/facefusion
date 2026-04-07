import os
import uuid
from typing import List

from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_415_UNSUPPORTED_MEDIA_TYPE

from facefusion import session_context, session_manager, state_manager
from facefusion.apis import asset_store
from facefusion.apis.asset_helper import save_asset_files, validate_asset_files
from facefusion.apis.endpoints.session import extract_access_token
from facefusion.filesystem import create_directory, remove_file
from facefusion.node import decode_vision_frame, encode_vision_frame
from facefusion.vision import read_video_frame


async def upload_asset(request : Request) -> Response:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)
	asset_type = request.query_params.get('type')

	if session_id and asset_type in [ 'source', 'target' ]:
		session_context.set_session_id(session_id)

		form = await request.form()
		upload_files = form.getlist('file')

		if upload_files and validate_asset_files(upload_files):
			asset_paths = await save_asset_files(upload_files)

			if asset_paths:
				asset_ids : List[str] = []

				for asset_path in asset_paths:
					asset = asset_store.create_asset(session_id, asset_type, asset_path)

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
					asset = asset_set.get(asset_id)

					if asset:
						remove_file(asset.get('path'))

			asset_store.delete_assets(session_id, asset_ids)
			return Response(status_code = HTTP_200_OK)

	return Response(status_code = HTTP_404_NOT_FOUND)


async def get_asset_frame(request : Request) -> Response:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)
	asset_id = request.path_params.get('asset_id')
	frame_number = int(request.path_params.get('frame_number', 0))

	if session_id and asset_id:
		asset = asset_store.get_asset(session_id, asset_id)

		if asset:
			asset_path = asset.get('path')

			if asset_path and os.path.exists(asset_path):
				frame = read_video_frame(asset_path, frame_number)

				if frame is not None:
					frame_b64 = encode_vision_frame(frame)
					return JSONResponse({ 'frame' : frame_b64 }, status_code = HTTP_200_OK)

	return Response(status_code = HTTP_404_NOT_FOUND)


async def assemble_video(request : Request) -> Response:
	import asyncio

	import cv2

	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)

	if not session_id:
		return Response(status_code = HTTP_400_BAD_REQUEST)

	session_context.set_session_id(session_id)
	body = await request.json()
	frames = body.get('frames', [])
	fps = body.get('fps', 30)

	if not frames:
		return Response(status_code = HTTP_400_BAD_REQUEST)

	temp_path = state_manager.get_temp_path()
	create_directory(temp_path)
	output_name = uuid.uuid4().hex + '.mp4'
	output_path = os.path.join(temp_path, output_name)

	first_frame = decode_vision_frame(frames[0])
	height, width = first_frame.shape[:2]
	fourcc = cv2.VideoWriter.fourcc(*'mp4v')

	def write_frames() -> bool:
		writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

		if not writer.isOpened():
			return False

		for frame_b64 in frames:
			frame = decode_vision_frame(frame_b64)

			if frame is not None:
				if frame.shape[:2] != (height, width):
					frame = cv2.resize(frame, (width, height))
				writer.write(frame)

		writer.release()
		return True

	success = await asyncio.to_thread(write_frames)

	if success and os.path.exists(output_path):
		asset = asset_store.create_asset(session_id, 'target', output_path)

		if asset:
			return JSONResponse({ 'asset_id' : asset.get('id') }, status_code = HTTP_201_CREATED)

	return Response(status_code = HTTP_400_BAD_REQUEST)
