from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from starlette.status import HTTP_204_NO_CONTENT

from facefusion import logger


async def root(request : Request) -> Response:
	logger.info(request.method + ' ' + request.url.path, __package__)

	return Response(status_code = HTTP_204_NO_CONTENT)


def create_api() -> Starlette:
	routes =\
	[
		Route('/', root)
	]

	return Starlette(routes = routes)
