import pytest
from starlette.testclient import TestClient

from facefusion import metadata, session_manager, state_manager
from facefusion.apis.core import create_api


@pytest.fixture(scope = 'module')
def test_client() -> TestClient:
	state_manager.init_item('execution_providers', [ 'cpu' ])

	with TestClient(create_api()) as test_client:
		yield test_client


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	session_manager.SESSIONS.clear()


def test_get_state(test_client : TestClient) -> None:
	get_state_response = test_client.get('/state')

	assert get_state_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	get_state_response = test_client.get('/state', headers =
	{
		'Authorization': 'Bearer ' + create_session_body.get('access_token')
	})
	get_state_body = get_state_response.json()

	assert get_state_body.get('execution_providers') == [ 'cpu' ]
	assert get_state_response.status_code == 200
