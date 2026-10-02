from functools import partial
from typing import Iterator, List

import anyio
import pytest
from starlette.testclient import TestClient
from starlette.types import Message

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


async def receive_disconnect() -> Message:
	return\
	{
		'type': 'http.disconnect'
	}


async def collect_message(messages : List[Message], message : Message) -> None:
	messages.append(message)


def test_create_exception_guard(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', content = 'invalid')
	create_session_body = create_session_response.json()

	assert create_session_body.get('message') == 'something went wrong'
	assert create_session_response.status_code == 400

	create_session_response = test_client.post('/session', content = bytes([ 255, 254, 253 ]), headers =
	{
		'Content-Type': 'application/json'
	})
	create_session_body = create_session_response.json()

	assert create_session_body.get('message') == 'something went wrong'
	assert create_session_response.status_code == 400

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	access_token = create_session_response.json().get('access_token')

	upload_response = test_client.post('/assets?type=source', content = 'invalid', headers =
	{
		'Authorization': 'Bearer ' + access_token,
		'Content-Type': 'multipart/form-data; boundary=invalid'
	})
	upload_body = upload_response.json()

	assert upload_body.get('message') == 'something went wrong'
	assert upload_response.status_code == 400

	set_state_response = test_client.put('/state', content = '{', headers =
	{
		'Authorization': 'Bearer ' + access_token,
		'Content-Type': 'application/json'
	})
	set_state_body = set_state_response.json()

	assert set_state_body.get('message') == 'something went wrong'
	assert set_state_response.status_code == 400

	messages : List[Message] = []
	scope =\
	{
		'type': 'http',
		'http_version': '1.1',
		'method': 'POST',
		'scheme': 'http',
		'path': '/session',
		'raw_path': '/session'.encode(),
		'root_path': '',
		'query_string': bytes(),
		'headers':
		[
			('content-type'.encode(), 'application/json'.encode())
		],
		'client': ('testclient', 50000),
		'server': ('testserver', 80)
	}

	session_manager.API_SESSIONS.clear()
	anyio.run(test_client.app, scope, receive_disconnect, partial(collect_message, messages))

	assert messages == []
	assert session_manager.API_SESSIONS == {}
