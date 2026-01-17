import subprocess
from typing import Iterator

import pytest
from starlette.testclient import TestClient

from facefusion import args_store, metadata, session_manager, state_manager
from facefusion.apis import asset_store
from facefusion.apis.core import create_api
from facefusion.download import conditional_download
from .helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vframes', '1', get_test_example_file('target-240p.jpg') ])


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	args_store.register_args([ 'source_paths', 'target_path' ], scopes = [ 'api' ])
	args_store.register_args([ 'execution_providers' ], scopes = [ 'api' ])
	state_manager.init_item('execution_providers', [ 'cpu' ])

	with TestClient(create_api()) as test_client:
		yield test_client


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	session_manager.SESSIONS.clear()
	asset_store.clear()


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


def test_set_state(test_client : TestClient) -> None:
	set_state_response = test_client.put('/state', json =
	{
		'execution_providers': [ 'cuda' ]
	})

	assert set_state_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	set_state_response = test_client.put('/state', json =
	{
		'execution_providers': [ 'cuda' ]
	}, headers =
	{
		'Authorization': 'Bearer ' + create_session_body.get('access_token')
	})
	set_state_body = set_state_response.json()

	assert set_state_body.get('execution_providers') == [ 'cuda' ]
	assert set_state_response.status_code == 200

	set_state_response = test_client.put('/state', json =
	{
		'invalid': 'invalid'
	}, headers =
	{
		'Authorization': 'Bearer ' + create_session_body.get('access_token')
	})
	set_state_body = set_state_response.json()

	assert set_state_body.get('invalid') is None
	assert set_state_response.status_code == 200


def test_select_source_assets(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})

	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')
	session_id = session_manager.find_session_id(access_token)
	source_paths =\
	[
		get_test_example_file('source.jpg'),
		get_test_example_file('source.jpg')
	]
	asset_ids =\
	[
		asset_store.create_asset(session_id, 'source', source_paths[0]).get('id'),
		asset_store.create_asset(session_id, 'source', source_paths[1]).get('id')
	]

	select_response = test_client.put('/state?action=select&type=source', json =
	{
		'asset_ids': asset_ids
	})

	assert select_response.status_code == 401

	select_response = test_client.put('/state?action=select&type=source', json =
	{
		'asset_ids': 'invalid'
	}, headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert select_response.status_code == 404

	select_response = test_client.put('/state?action=select&type=source', json =
	{
		'asset_ids': asset_ids
	}, headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	select_body = select_response.json()

	assert select_body.get('source_paths') == source_paths
	assert select_response.status_code == 200


def test_select_target_assets(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')
	session_id = session_manager.find_session_id(access_token)
	target_path = get_test_example_file('target-240p.jpg')
	asset_id = asset_store.create_asset(session_id, 'target', target_path).get('id')

	select_response = test_client.put('/state?action=select&type=target', json=
	{
		'asset_id': asset_id
	})

	assert select_response.status_code == 401

	select_response = test_client.put('/state?action=select&type=target', json =
	{
		'asset_id': 'invalid'
	}, headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert select_response.status_code == 404

	select_response = test_client.put('/state?action=select&type=target', json =
	{
		'asset_id': asset_id
	}, headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	select_body = select_response.json()

	assert select_body.get('target_path') == target_path
	assert select_response.status_code == 200
