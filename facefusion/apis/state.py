from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from facefusion import logger
from facefusion import state_manager


async def get_state(request : Request) -> Response:
	logger.info('GET ' + request.url.path, __package__)

	return JSONResponse(state_manager.get_state(), status_code = HTTP_200_OK)


async def set_state(request : Request) -> Response:
	logger.info('PUT ' + request.url.path, __package__)
	body = await request.json()

	for key, value in body.items():
		state_manager.set_item(key, value)

	return JSONResponse(state_manager.get_state(), status_code = HTTP_200_OK)

