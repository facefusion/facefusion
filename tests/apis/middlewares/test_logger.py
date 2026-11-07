import logging

from _pytest.logging import LogCaptureFixture
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from facefusion.apis.middlewares.logger import create_logger


def get_root(request : Request) -> PlainTextResponse:
	return PlainTextResponse('root', status_code = 201)


def test_create_logger(caplog : LogCaptureFixture) -> None:
	caplog.set_level(logging.INFO, logger = 'facefusion')
	api = Starlette(routes = [ Route('/', get_root, methods = [ 'POST' ]) ])
	api.add_middleware(create_logger)

	with TestClient(api) as test_client:
		test_client.post('/')

	assert caplog.messages == [ 'post / 201' ]
	assert caplog.records[0].__dict__.get('module_name') == 'facefusion.apis.request'
