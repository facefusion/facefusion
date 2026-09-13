from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK

from facefusion import metadata


async def get_root(request : Request) -> JSONResponse:
	root =\
	{
		'name': metadata.get('name'),
		'version': metadata.get('version')
	}
	return JSONResponse(root, status_code = HTTP_200_OK)
