import signal
from typing import Iterator
from unittest.mock import Mock, patch

import pytest
from starlette.testclient import TestClient

from facefusion import process_manager, session_context, state_manager
from facefusion.apis.core import create_api, create_server, start_server, stop_server


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('cors_origins', [ 'http://localhost:7000' ])
	state_manager.init_item('api_host', '127.0.0.1')
	state_manager.init_item('api_port', 7000)
	state_manager.init_item('api_session_limit', 4)
	state_manager.init_item('api_upload_limit', 512)

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

	state_manager.set_item('api_upload_limit', 1)

	with TestClient(create_api()) as upload_limit_client:
		session_response = upload_limit_client.post('/session', content = bytes(1024 * 1024))

		assert not session_response.status_code == 413

		session_response = upload_limit_client.post('/session', content = bytes(1024 * 1024 + 1))

		assert session_response.status_code == 413

	state_manager.set_item('api_upload_limit', 512)


def test_create_server() -> None:
	server = create_server()

	assert server.config.host == '127.0.0.1'
	assert server.config.port == 7000
	assert server.config.limit_concurrency == 32
	assert server.should_exit is False


def test_start_server() -> None:
	server_mock = Mock()
	server_mock.should_exit = True

	with patch('facefusion.apis.core.signal.signal') as signal_mock:
		assert start_server(server_mock) == 0

		sigint_call, sigterm_call = signal_mock.call_args_list

		assert sigint_call.args[0] == signal.SIGINT
		assert sigint_call.args[1].func is stop_server
		assert sigterm_call.args[0] == signal.SIGTERM
		assert sigterm_call.args[1].func is stop_server
		assert server_mock.run.call_count == 1

		server_mock.should_exit = False

		assert start_server(server_mock) == 1


def test_stop_server() -> None:
	server = create_server()
	process_manager.start()
	stop_server(server, signal.SIGINT, None)

	assert process_manager.is_stopping() is True
	assert server.should_exit is True
	assert server.force_exit is False

	stop_server(server, signal.SIGINT, None)

	assert server.force_exit is True
