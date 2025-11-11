import os

import pytest
from starlette.testclient import TestClient

from facefusion import metadata, session_manager
from facefusion.apis.core import create_api


@pytest.fixture(scope = 'module')
def test_client():
	with TestClient(create_api()) as test_client:
		yield test_client


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	session_manager.SESSIONS.clear()


def test_create_session(test_client : TestClient) -> None:
	create_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_data = create_response.json()

	assert session_manager.get_session(create_data.get('access_token'))
	assert session_manager.get_session(create_data.get('refresh_token'))
	assert create_response.status_code == 201

	create_response = test_client.post('/session', json =
	{
		'api_key': 'TEST',
		'client_version': metadata.get('version')
	})

	assert create_response.status_code == 401

	os.environ['FACEFUSION_API_KEY'] = 'TEST'
	create_response = test_client.post('/session', json =
	{
		'api_key': 'INVALID',
		'client_version': metadata.get('version')
	})

	assert create_response.status_code == 401

	os.environ['FACEFUSION_API_KEY'] = 'TEST'
	create_response = test_client.post('/session', json =
	{
		'api_key': 'TEST',
		'client_version': metadata.get('version')
	})

	assert create_response.status_code == 201

	del os.environ['FACEFUSION_API_KEY']


def test_get_session(test_client : TestClient) -> None:
	get_response = test_client.get('/session')

	assert get_response.status_code == 401

	create_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_data = create_response.json()

	get_response = test_client.get('/session', headers =
	{
		'Authorization': 'Bearer ' + create_data.get('access_token')
	})

	assert get_response.status_code == 200


def test_refresh_session(test_client : TestClient) -> None:
	create_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_data = create_response.json()

	refresh_response = test_client.put('/session', json =
	{
		'refresh_token': 'INVALID'
	})

	assert refresh_response.status_code == 401

	refresh_response = test_client.put('/session', json =
	{
		'refresh_token': create_data.get('refresh_token')
	})
	refresh_data = refresh_response.json()

	assert not session_manager.get_session(create_data.get('access_token'))
	assert not session_manager.get_session(create_data.get('refresh_token'))

	assert session_manager.get_session(refresh_data.get('access_token'))
	assert session_manager.get_session(refresh_data.get('refresh_token'))

	assert refresh_response.status_code == 200


def test_destroy_session(test_client : TestClient) -> None:
	create_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_data = create_response.json()

	delete_response = test_client.delete('/session', headers =
	{
		'Authorization': 'Bearer INVALID'
	})

	assert delete_response.status_code == 401

	delete_response = test_client.delete('/session', headers =
	{
		'Authorization': 'Bearer ' + create_data.get('access_token')
	})

	assert not session_manager.get_session(create_data.get('access_token'))
	assert not session_manager.get_session(create_data.get('refresh_token'))

	assert delete_response.status_code == 204
