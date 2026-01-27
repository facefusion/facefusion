import tempfile
from typing import Iterator

import pytest
from starlette.testclient import TestClient

from facefusion import metadata, session_manager, state_manager
from facefusion.apis.core import create_api


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	with TestClient(create_api()) as test_client:
		yield test_client


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	state_manager.init_item('temp_path', tempfile.gettempdir())
	session_manager.SESSIONS.clear()


def test_get_metrics(test_client : TestClient) -> None:
	get_response = test_client.get('/metrics')

	assert get_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	get_response = test_client.get('/metrics', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	get_body = get_response.json()

	assert get_response.status_code == 200
	assert 'execution_devices' in get_body
	assert 'memory' in get_body
	assert 'disk' in get_body

	memory = get_body.get('memory')

	assert 'total' in memory
	assert 'free' in memory
	assert 'utilization' in memory
	assert memory.get('total').get('unit') == 'GiB'
	assert memory.get('free').get('unit') == 'GiB'
	assert memory.get('utilization').get('unit') == '%'
