from typing import Iterator

import pytest
from starlette.testclient import TestClient

from facefusion import metadata, session_manager
from facefusion.apis.core import create_api


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	with TestClient(create_api()) as test_client:
		yield test_client


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	session_manager.SESSIONS.clear()


def test_get_metrics(test_client : TestClient) -> None:
	get_metrics_response = test_client.get('/metrics')

	assert get_metrics_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	get_metrics_response = test_client.get('/metrics', headers =
	{
		'Authorization': 'Bearer ' + create_session_body.get('access_token')
	})
	get_metrics_body = get_metrics_response.json()

	assert 'execution_devices' in get_metrics_body
	assert isinstance(get_metrics_body.get('execution_devices'), list)
	assert get_metrics_response.status_code == 200


def test_websocket_metrics(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	with test_client.websocket_connect('/metrics', subprotocols =
	[
		'access_token.' + create_session_body.get('access_token')
	]) as websocket:
		metrics_set = websocket.receive_json()

		assert 'execution_devices' in metrics_set
		assert isinstance(metrics_set.get('execution_devices'), list)
