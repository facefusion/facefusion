from typing import Iterator

import pytest
from starlette.testclient import TestClient

from facefusion import metadata, session_manager, state_manager
from facefusion.apis.core import create_api
from .assert_helper import get_test_jobs_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('jobs_path', get_test_jobs_directory())
	state_manager.init_item('api_session_limit', 10)


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	session_manager.API_SESSIONS.clear()


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	with TestClient(create_api()) as test_client:
		yield test_client


def test_ping(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	with test_client.websocket_connect('/ping', subprotocols =
	[
		'access_token.' + create_session_body.get('access_token')
	]) as websocket:
		assert websocket
