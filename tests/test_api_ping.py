from datetime import timedelta
from typing import Iterator

import pytest
from starlette.testclient import TestClient, WebSocketDenialResponse

from facefusion import metadata, session_manager, state_manager
from facefusion.apis import websocket_store
from facefusion.apis.core import create_api
from facefusion.types import ApiSession
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
		assert websocket.accepted_subprotocol == 'access_token.' + create_session_body.get('access_token')

		websocket_store.destroy(session_manager.find_api_session_id(create_session_body.get('access_token')))

		assert websocket.receive() == { 'type': 'websocket.close', 'code': 1000, 'reason': '' }

	for subprotocols in [ [], [ 'access_token.invalid' ], [ 'refresh_token.' + create_session_body.get('refresh_token') ] ]:
		with pytest.raises(WebSocketDenialResponse) as websocket_denial:
			with test_client.websocket_connect('/ping', subprotocols = subprotocols):
				pass

		assert websocket_denial.value.json().get('message') == 'invalid access token'
		assert websocket_denial.value.status_code == 401

	with pytest.raises(WebSocketDenialResponse) as websocket_denial:
		with test_client.websocket_connect('/ping', headers =
		{
			'Authorization': 'Bearer ' + create_session_body.get('access_token')
		}):
			pass

	assert websocket_denial.value.status_code == 401

	session_id = session_manager.find_api_session_id(create_session_body.get('access_token'))
	session : ApiSession = session_manager.get_api_session(session_id)
	session_manager.set_api_session(session_id,
	{
		'access_token': session.get('access_token'),
		'refresh_token': session.get('refresh_token'),
		'created_at': session.get('created_at'),
		'expires_at': session.get('expires_at') - timedelta(hours = 1)
	})

	with pytest.raises(WebSocketDenialResponse) as websocket_denial:
		with test_client.websocket_connect('/ping', subprotocols =
		[
			'access_token.' + create_session_body.get('access_token')
		]):
			pass

	assert websocket_denial.value.status_code == 426
