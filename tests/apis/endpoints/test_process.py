from typing import Iterator

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from facefusion import metadata, process_manager, session_context, session_manager, state_manager
from facefusion.apis import websocket_manager
from facefusion.apis.core import create_api
from tests.assert_helper import get_test_jobs_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('jobs_path', get_test_jobs_directory())
	state_manager.init_item('api_session_limit', 10)
	state_manager.init_item('api_upload_limit', 512)


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = session_context.resolve_local_id()

	session_context.set_session_id(local_id)
	session_manager.API_SESSIONS.clear()

	yield

	session_context.set_session_id(local_id)


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	with TestClient(create_api()) as test_client:
		yield test_client


def test_websocket_process(test_client : TestClient) -> None:
	with pytest.raises(WebSocketDisconnect):
		test_client.websocket_connect('/process').__enter__()

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	session_id = session_manager.find_api_session_id(create_session_body.get('access_token'))

	with test_client.websocket_connect('/process', subprotocols =
	[
		'access_token.' + create_session_body.get('access_token')
	]) as websocket:
		assert websocket.receive_json() ==\
		{
			'session':
			{
				'status': 'pending',
				'stages': []
			}
		}

		session_context.set_session_id(session_id)
		process_manager.start()
		process_manager.stage('stream', 'streaming',
		{
			'unit': 'frame',
			'current': 0,
			'started_at': 10.0,
			'updated_at': 10.0
		})

		assert websocket.receive_json() ==\
		{
			'session':
			{
				'status': 'processing',
				'stages':
				[
					{
						'type': 'stream',
						'title': 'streaming',
						'progress':
						{
							'unit': 'frame',
							'current': 0,
							'started_at': 10.0,
							'updated_at': 10.0
						}
					}
				]
			}
		}

		session_manager.fork_session()
		process_manager.start()
		process_manager.stage('infer', 'processing',
		{
			'unit': 'frame',
			'current': 0,
			'total': 100,
			'started_at': 20.0,
			'updated_at': 20.0
		})

		assert websocket.receive_json() ==\
		{
			'session':
			{
				'status': 'processing',
				'stages':
				[
					{
						'type': 'stream',
						'title': 'streaming',
						'progress':
						{
							'unit': 'frame',
							'current': 0,
							'started_at': 10.0,
							'updated_at': 10.0
						}
					}
				]
			},
			'fork':
			{
				'status': 'processing',
				'stages':
				[
					{
						'type': 'infer',
						'title': 'processing',
						'progress':
						{
							'unit': 'frame',
							'current': 0,
							'total': 100,
							'started_at': 20.0,
							'updated_at': 20.0
						}
					}
				]
			}
		}

		process_manager.end()
		session_manager.join_session()
		process_manager.end()
		websocket_manager.destroy(session_id)

		assert websocket.receive() == { 'type': 'websocket.close', 'code': 1000, 'reason': '' }
