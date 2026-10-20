from typing import Iterator

import pytest
from starlette.testclient import TestClient

from facefusion import state_manager
from facefusion.apis.core import create_api


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('api_origin', 'http://localhost:7000')


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
