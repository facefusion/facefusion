from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_CONTENT

from facefusion import args_helper, state_manager, translator
from facefusion.apis import asset_store
from facefusion.apis.state_helper import normalize_argument_value, validate_argument_key, validate_argument_value


async def get_state(request : Request) -> JSONResponse:
	api_args = args_helper.extract_api_args(state_manager.get_state())
	return JSONResponse(state_manager.collect_state(api_args), status_code = HTTP_200_OK)


async def set_state(request : Request) -> Response:
	__api_args__ = {}

	action = request.query_params.get('action')
	asset_type = request.query_params.get('type')

	if action == 'select' and asset_type == 'source':
		return await select_source(request)

	if action == 'select' and asset_type == 'target':
		return await select_target(request)

	body = await request.json()

	for key, value in body.items():
		if not validate_argument_key(key):
			return JSONResponse(
			{
				'message': translator.get('invalid_state_key', 'facefusion.apis')
			}, status_code = HTTP_400_BAD_REQUEST)

		__value__ = normalize_argument_value(key, value)

		if not validate_argument_value(key, __value__):
			return JSONResponse(
			{
				'message': translator.get('invalid_state_value', 'facefusion.apis')
			}, status_code = HTTP_400_BAD_REQUEST)

		__api_args__[key] = __value__

	if __api_args__:

		for key, value in __api_args__.items():
			state_manager.set_item(key, value)

		__api_args__ = args_helper.extract_api_args(state_manager.get_state())
		return JSONResponse(state_manager.collect_state(__api_args__), status_code = HTTP_200_OK)

	return Response(status_code = HTTP_422_UNPROCESSABLE_CONTENT)


async def select_source(request : Request) -> JSONResponse:
	body = await request.json()
	asset_ids = body.get('asset_ids')

	if isinstance(asset_ids, list):
		source_paths = []

		for asset_id in asset_ids:
			asset = asset_store.get_asset(asset_id)

			if asset:
				source_paths.append(asset.get('path'))

		state_manager.set_item('source_paths', source_paths)

		__api_args__ = args_helper.extract_api_args(state_manager.get_state())
		return JSONResponse(state_manager.collect_state(__api_args__), status_code = HTTP_200_OK)

	return JSONResponse(
	{
		'message': translator.get('source_asset_not_found', 'facefusion.apis')
	}, status_code = HTTP_404_NOT_FOUND)


async def select_target(request : Request) -> JSONResponse:
	body = await request.json()
	asset_id = body.get('asset_id')

	if isinstance(asset_id, str):
		asset = asset_store.get_asset(asset_id)

		if asset:
			state_manager.set_item('target_path', asset.get('path'))

			__api_args__ = args_helper.extract_api_args(state_manager.get_state())
			return JSONResponse(state_manager.collect_state(__api_args__), status_code = HTTP_200_OK)

	return JSONResponse(
	{
		'message': translator.get('target_asset_not_found', 'facefusion.apis')
	}, status_code = HTTP_404_NOT_FOUND)
