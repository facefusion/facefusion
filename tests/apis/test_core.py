import signal
from typing import Iterator

import pytest
from starlette.testclient import TestClient

from facefusion import process_manager, session_context, state_manager
from facefusion.apis.core import create_api, create_server, stop_server


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('cors_origins', [ 'http://localhost:7000' ])
	state_manager.init_item('api_host', '127.0.0.1')
	state_manager.init_item('api_port', 7000)
	state_manager.init_item('api_session_limit', 4)

	local_id = session_context.resolve_local_id()
	session_context.set_session_id(local_id)
	process_manager.clear()


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	with TestClient(create_api()) as test_client:
		yield test_client


def test_create_api(test_client : TestClient) -> None:
	session_response = test_client.options('/session', headers =
	{
		'Origin': 'http://localhost:7000',
		'Access-Control-Request-Method': 'GET',
		'Access-Control-Request-Headers': 'Authorization'
	})

	assert session_response.headers.get('access-control-allow-origin') == 'http://localhost:7000'
	assert session_response.status_code == 200

	session_response = test_client.options('/session', headers =
	{
		'Origin': 'invalid',
		'Access-Control-Request-Method': 'GET',
		'Access-Control-Request-Headers': 'Authorization'
	})

	assert session_response.headers.get('access-control-allow-origin') is None
	assert session_response.status_code == 400

	root_response = test_client.get('/', headers =
	{
		'Origin': 'http://localhost:7000'
	})

	assert root_response.headers.get('access-control-expose-headers') == 'Location'
	assert root_response.status_code == 200


def test_create_server() -> None:
	server = create_server()

	assert server.config.host == '127.0.0.1'
	assert server.config.port == 7000
	assert server.config.limit_concurrency == 32
	assert server.should_exit is False


def test_stop_server() -> None:
	server = create_server()
	process_manager.start()
	stop_server(server, signal.SIGINT, None)

	assert process_manager.is_stopping() is True
	assert server.should_exit is True
	assert server.force_exit is False

	stop_server(server, signal.SIGINT, None)

	assert server.force_exit is True
