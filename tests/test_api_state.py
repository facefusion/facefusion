from typing import Iterator

import pytest
from starlette.testclient import TestClient

from facefusion import args_store, metadata, session_manager, state_manager
from facefusion.apis import asset_store
from facefusion.apis.core import create_api


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
	asset_id_1 = asset_store.register_asset('/path/to/source1.jpg')
	asset_id_2 = asset_store.register_asset('/path/to/source2.jpg')

	select_response = test_client.put('/state?action=select&type=source', json =
	{
		'asset_ids': [ asset_id_1, asset_id_2 ]
	})

	assert select_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	select_response = test_client.put('/state?action=select&type=source', json =
	{
		'asset_ids': 'invalid_string_not_list'
	}, headers =
	{
		'Authorization': 'Bearer ' + create_session_body.get('access_token')
	})

	assert select_response.status_code == 404

	select_response = test_client.put('/state?action=select&type=source', json =
	{
		'asset_ids': [ asset_id_1, asset_id_2 ]
	}, headers =
	{
		'Authorization': 'Bearer ' + create_session_body.get('access_token')
	})
	select_body = select_response.json()

	assert select_body.get('source_paths') == [ '/path/to/source1.jpg', '/path/to/source2.jpg' ]
	assert select_response.status_code == 200


def test_select_target_assets(test_client : TestClient) -> None:
	asset_id_1 = asset_store.register_asset('/path/to/target1.jpg')

	select_response = test_client.put('/state?action=select&type=target', json =
	{
		'asset_id': asset_id_1
	})

	assert select_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	select_response = test_client.put('/state?action=select&type=target', json =
	{
		'asset_id': 'invalid_asset_id'
	}, headers =
	{
		'Authorization': 'Bearer ' + create_session_body.get('access_token')
	})

	assert select_response.status_code == 404

	select_response = test_client.put('/state?action=select&type=target', json =
	{
		'asset_id': asset_id_1
	}, headers =
	{
		'Authorization': 'Bearer ' + create_session_body.get('access_token')
	})
	select_body = select_response.json()

	assert select_body.get('target_path') == '/path/to/target1.jpg'
	assert select_response.status_code == 200
