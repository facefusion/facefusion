import os
import tempfile
from datetime import timedelta
from typing import Iterator
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from facefusion import content_store, face_store, inference_manager, metadata, process_manager, rtc_store, session_context, session_manager, state_manager, store_creator, store_manager, video_manager
from facefusion.apis import asset_store, websocket_store
from facefusion.apis.core import create_api
from facefusion.download import conditional_download
from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import ApiSession
from .assert_helper import get_test_example_file, get_test_examples_directory, get_test_jobs_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()

	datachannel_module.pre_check()

	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg'
	])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = session_context.resolve_local_id()

	session_context.set_session_id(local_id)
	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('jobs_path', get_test_jobs_directory())
	state_manager.init_item('api_session_limit', 10)
	session_manager.API_SESSIONS.clear()
	asset_store.delete_assets()

	yield

	session_context.set_session_id(local_id)


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

	assert test_client.post('/session', content = 'invalid').status_code == 400


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

	session_id = session_manager.find_api_session_id(create_session_body.get('access_token'))
	session : ApiSession = session_manager.get_api_session(session_id)
	session_manager.set_api_session(session_id,
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
	session_id = session_manager.find_api_session_id(access_token)
	session_context.set_session_id(session_id)
	session_manager.fork_session()

	refresh_session_response = test_client.put('/session', json = {})

	assert refresh_session_response.status_code == 401

	session_manager.join_session()

	refresh_session_response = test_client.put('/session', json =
	{
		'refresh_token': create_session_body.get('refresh_token')
	})
	refresh_session_body = refresh_session_response.json()

	assert refresh_session_body.get('access_token')
	assert refresh_session_body.get('refresh_token')
	assert session_manager.find_api_session_id(access_token) is None
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

	session_id = session_manager.find_api_session_id(create_session_body.get('access_token'))
	session : ApiSession = session_manager.get_api_session(session_id)
	session_manager.set_api_session(session_id,
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

	assert test_client.put('/session', content = 'invalid').status_code == 400


def test_destroy_session(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	access_token = create_session_response.json().get('access_token')
	session_id = session_manager.find_api_session_id(access_token)
	jobs_path = os.path.join(get_test_jobs_directory(), session_id)

	delete_session_response = test_client.delete('/session', headers =
	{
		'Authorization': 'Bearer INVALID'
	})

	assert os.path.isdir(jobs_path) is True
	assert delete_session_response.status_code == 401

	delete_session_response = test_client.delete('/session', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert os.path.isdir(jobs_path) is False
	assert session_manager.find_api_session_id(access_token) is None
	assert delete_session_response.status_code == 200

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	access_token = create_session_response.json().get('access_token')
	session_id = session_manager.find_api_session_id(access_token)
	session_context.set_session_id(session_id)
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

	for asset in asset_store.get_assets().values():
		asset_paths.append(asset.get('path'))

	with patch('facefusion.apis.endpoints.session.remove_directory', return_value = False):
		delete_session_response = test_client.delete('/session', headers =
		{
			'Authorization': 'Bearer ' + access_token
		})

	for asset_path in asset_paths:
		assert os.path.exists(asset_path) is True

	assert delete_session_response.json().get('message') == 'directory not removed'
	assert session_manager.find_api_session_id(access_token) == session_id
	assert delete_session_response.status_code == 404

	delete_session_response = test_client.delete('/session', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert session_manager.find_api_session_id(access_token) is None
	assert store_creator.has_content(asset_store.ASSET_STORE, session_id) is False
	assert delete_session_response.status_code == 200

	for asset_path in asset_paths:
		assert os.path.exists(asset_path) is False


def test_destroy_session_content(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	access_token = create_session_response.json().get('access_token')
	session_id = session_manager.find_api_session_id(access_token)
	session : ApiSession = session_manager.get_api_session(session_id)
	local_id = session_context.resolve_local_id()

	stores =\
	[
		(state_manager, state_manager.STATE_SET),
		(asset_store, asset_store.ASSET_STORE),
		(content_store, content_store.CONTENT_STORE),
		(face_store, face_store.FACE_STORE),
		(inference_manager, inference_manager.INFERENCE_POOL_STORE),
		(process_manager, process_manager.PROCESS_STORE),
		(rtc_store, rtc_store.RTC_STORE),
		(video_manager, video_manager.VIDEO_POOL_STORE),
		(websocket_store, websocket_store.WEBSOCKET_STORE)
	]

	session_manager.set_api_session(session_id,
	{
		'access_token': session.get('access_token'),
		'refresh_token': session.get('refresh_token'),
		'created_at': session.get('created_at'),
		'expires_at': session.get('expires_at') - timedelta(hours = 1)
	})

	for session_module, store in stores:
		assert store_creator.has_content(store, session_id) is True

	store_manager.destroy(session_id)
	session_manager.conditional_clear_api_session(session_id)

	for session_module, store in stores:
		assert store_creator.has_content(store, session_id) is False

		session_module.destroy(session_id)

		assert store_creator.has_content(store, session_id) is False

	assert store_creator.has_content(state_manager.STATE_SET, local_id) is True
	assert session_manager.get_api_session(session_id) is None
