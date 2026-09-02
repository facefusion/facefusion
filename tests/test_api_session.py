import os
import tempfile
from datetime import timedelta
from typing import Iterator

import pytest
from starlette.testclient import TestClient

from facefusion import metadata, process_manager, session_manager, state_manager
from facefusion.apis import asset_store
from facefusion.apis.core import create_api
from facefusion.download import conditional_download
from facefusion.types import Session
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg'
	])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	state_manager.init_item('temp_path', tempfile.gettempdir())
	session_manager.SESSIONS.clear()
	asset_store.clear()


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	with TestClient(create_api()) as test_client:
		yield test_client


def test_create_session(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	assert create_session_body.get('access_token')
	assert create_session_body.get('refresh_token')
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

	session_id = session_manager.find_session_id(create_session_body.get('access_token'))
	session : Session = session_manager.get_session(session_id)
	session_manager.set_session(session_id,
	{
		'access_token': session.get('access_token'),
		'refresh_token': session.get('refresh_token'),
		'created_at': session.get('created_at'),
		'expires_at': session.get('expires_at') - timedelta(hours = 1)
	})

	get_session_response = test_client.get('/session', headers =
	{
		'Authorization': 'Bearer ' + create_session_body.get('access_token')
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

	access_token = create_session_body.get('access_token')

	refresh_session_response = test_client.put('/session', json =
	{
		'refresh_token': create_session_body.get('refresh_token')
	})
	refresh_session_body = refresh_session_response.json()

	assert refresh_session_body.get('access_token')
	assert refresh_session_body.get('refresh_token')
	assert session_manager.find_session_id(access_token) is None
	assert refresh_session_response.status_code == 200

	refresh_session_response = test_client.put('/session', json =
	{
		'refresh_token': create_session_body.get('refresh_token')
	})

	assert refresh_session_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	session_id = session_manager.find_session_id(create_session_body.get('access_token'))
	session : Session = session_manager.get_session(session_id)
	session_manager.set_session(session_id,
	{
		'access_token': session.get('access_token'),
		'refresh_token': session.get('refresh_token'),
		'created_at': session.get('created_at'),
		'expires_at': session.get('expires_at') - timedelta(hours = 1)
	})

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
	access_token = create_session_body.get('access_token')
	session_id = session_manager.find_session_id(access_token)
	source_path = get_test_example_file('source.jpg')

	with open(source_path, 'rb') as source_file:
		test_client.post('/assets?type=source', headers =
		{
			'Authorization': 'Bearer ' + access_token
		}, files =
		[
			('file', ('source.jpg', source_file.read(), 'image/jpeg'))
		])

	asset_paths = []

	for asset in asset_store.get_assets(session_id).values():
		asset_paths.append(asset.get('path'))

	delete_session_response = test_client.delete('/session', headers =
	{
		'Authorization': 'Bearer INVALID'
	})

	assert delete_session_response.status_code == 401

	for asset_path in asset_paths:
		assert os.path.exists(asset_path) is True

	delete_session_response = test_client.delete('/session', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert session_manager.find_session_id(access_token) is None
	assert asset_store.get_assets(session_id) is None
	assert delete_session_response.status_code == 200

	for asset_path in asset_paths:
		assert os.path.exists(asset_path) is False
