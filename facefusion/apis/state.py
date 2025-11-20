from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK

from facefusion import args_store, state_manager


async def get_state(request : Request) -> JSONResponse:
	api_args = args_store.filter_api_args(state_manager.get_state())
	return JSONResponse(state_manager.collect_state(api_args), status_code = HTTP_200_OK)


async def set_state(request : Request) -> JSONResponse:
	body = await request.json()
	api_keys = args_store.get_api_keys()

	for key, value in body.items():
		if key in api_keys:
			state_manager.set_item(key, value)

	api_args = args_store.filter_api_args(state_manager.get_state())
	return JSONResponse(state_manager.collect_state(api_args), status_code = HTTP_200_OK)

