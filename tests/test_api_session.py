import os
from datetime import timedelta
from typing import Iterator

import pytest
from starlette.testclient import TestClient

from facefusion import metadata, session_manager
from facefusion.apis.core import create_api
from facefusion.types import Session


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	with TestClient(create_api()) as test_client:
		yield test_client


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	session_manager.SESSIONS.clear()


def test_create_session(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	assert session_manager.get_session(create_session_body.get('access_token'))
	assert create_session_response.status_code == 201

	create_session_response = test_client.post('/session', json =
	{
		'api_key': 'TEST',
		'client_version': metadata.get('version')
	})

	assert create_session_response.status_code == 401

	os.environ['FACEFUSION_API_KEY'] = 'TEST'
	create_session_response = test_client.post('/session', json =
	{
		'api_key': 'INVALID',
		'client_version': metadata.get('version')
	})

	assert create_session_response.status_code == 401

	os.environ['FACEFUSION_API_KEY'] = 'TEST'
	create_session_response = test_client.post('/session', json =
	{
		'api_key': 'TEST',
		'client_version': metadata.get('version')
	})

	assert create_session_response.status_code == 201

	del os.environ['FACEFUSION_API_KEY']


def test_get_session(test_client : TestClient) -> None:
	get_session_response = test_client.get('/session')

	assert get_session_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	get_session_response = test_client.get('/session', headers =
	{
		'Authorization': 'Bearer ' + create_session_body.get('access_token')
	})

	assert get_session_response.status_code == 200

	access_token = create_session_body.get('access_token')
	session : Session = session_manager.get_session(access_token)
	session_manager.set_session(access_token,
	{
		'access_token': session.get('access_token'),
		'refresh_token': session.get('refresh_token'),
		'created_at': session.get('created_at'),
		'expires_at': session.get('expires_at') - timedelta(hours = 1)
	})

	get_session_response = test_client.get('/session', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert get_session_response.status_code == 426


def test_refresh_session(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	refresh_session_response = test_client.put('/session', json =
	{
		'refresh_token': 'INVALID'
	})

	assert refresh_session_response.status_code == 401

	refresh_session_response = test_client.put('/session', json =
	{
		'refresh_token': create_session_body.get('refresh_token')
	})
	refresh_session_body = refresh_session_response.json()

	assert session_manager.get_session(create_session_body.get('access_token')) is None

	assert session_manager.get_session(refresh_session_body.get('access_token'))

	assert refresh_session_response.status_code == 200

	refresh_session_response = test_client.put('/session', json =
	{
		'refresh_token': create_session_body.get('refresh_token')
	})

	assert refresh_session_response.status_code == 401


def test_destroy_session(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	delete_session_response = test_client.delete('/session', headers =
	{
		'Authorization': 'Bearer INVALID'
	})

	assert delete_session_response.status_code == 401

	delete_session_response = test_client.delete('/session', headers =
	{
		'Authorization': 'Bearer ' + create_session_body.get('access_token')
	})

	assert session_manager.get_session(create_session_body.get('access_token')) is None

	assert delete_session_response.status_code == 200
