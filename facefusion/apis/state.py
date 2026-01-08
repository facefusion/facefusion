from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from facefusion import args_store, state_manager, translator
from facefusion.apis import asset_store


async def get_state(request : Request) -> JSONResponse:
	api_args = args_store.filter_api_args(state_manager.get_state()) #type:ignore[arg-type]
	return JSONResponse(state_manager.collect_state(api_args), status_code = HTTP_200_OK)


async def set_state(request : Request) -> JSONResponse:
	body = await request.json()
	action = request.query_params.get('action')

	if action == 'select':
		asset_type = request.query_params.get('type')

		if asset_type and asset_type in [ 'source', 'target' ]:

			if asset_type == 'source':
				asset_ids = body.get('asset_ids')

				if isinstance(asset_ids, list):
					source_paths = []

					for asset_id in asset_ids:
						asset = asset_store.get_asset(asset_id)

						if not asset:
							return JSONResponse(
							{
								'message': translator.get('source_asset_not_found', __package__)
							}, status_code = HTTP_404_NOT_FOUND)

						source_paths.append(asset.get('path'))

					state_manager.set_item('source_paths', source_paths)

					__api_args__ = args_store.filter_api_args(state_manager.get_state()) #type:ignore[arg-type]
					return JSONResponse(state_manager.collect_state(__api_args__), status_code = HTTP_200_OK)

			if asset_type == 'target':
				asset_id = body.get('asset_id')

				if isinstance(asset_id, str):
					asset = asset_store.get_asset(asset_id)

					if not asset:
						return JSONResponse(
						{
							'message': translator.get('target_asset_not_found', __package__)
						}, status_code = HTTP_404_NOT_FOUND)

					state_manager.set_item('target_path', asset.get('path'))

					__api_args__ = args_store.filter_api_args(state_manager.get_state()) #type:ignore[arg-type]
					return JSONResponse(state_manager.collect_state(__api_args__), status_code = HTTP_200_OK)

	api_args = args_store.get_api_args()

	for key, value in body.items():
		if key in api_args:
			state_manager.set_item(key, value)

	__api_args__ = args_store.filter_api_args(state_manager.get_state()) #type:ignore[arg-type]
	return JSONResponse(state_manager.collect_state(__api_args__), status_code = HTTP_200_OK)
