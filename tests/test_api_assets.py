import tempfile
from typing import Iterator

import pytest
from starlette.testclient import TestClient

from facefusion import metadata, session_manager, state_manager
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


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	with TestClient(create_api()) as test_client:
		yield test_client


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('temp_frame_format', 'png')
	session_manager.SESSIONS.clear()
	asset_store.clear()


def test_upload_asset(test_client : TestClient) -> None:
	upload_response = test_client.post('/assets?type=source')

	assert upload_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')
	session_id = session_manager.find_session_id(access_token)

	source_path = get_test_example_file('source.jpg')
	target_path = get_test_example_file('target-240p.mp4')

	with open(source_path, 'rb') as source_file, open(target_path, 'rb') as target_file:
		source_content = source_file.read()
		target_content = target_file.read()
		upload_response = test_client.post('/assets?type=source', headers =
		{
			'Authorization': 'Bearer ' + access_token
		}, files =
		[
			('file', ('source.jpg', source_content, 'image/jpeg')),
			('file', ('target.mp4', target_content, 'video/mp4'))
		])
	upload_body = upload_response.json()
	asset_ids = upload_body.get('asset_ids')

	asset = asset_store.get_asset(session_id, asset_ids[0])

	assert asset.get('media') == 'image'
	assert asset.get('type') == 'source'
	assert asset.get('format') == 'jpeg'

	asset = asset_store.get_asset(session_id, asset_ids[1])

	assert asset.get('media') == 'video'
	assert asset.get('type') == 'source'
	assert asset.get('format') == 'mp4'

	assert upload_response.status_code == 201

	upload_response = test_client.post('/assets?type=invalid', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert upload_response.status_code == 400

	upload_response = test_client.post('/assets?type=source', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert upload_response.status_code == 400

	upload_response = test_client.post('/assets?type=source', headers =
	{
		'Authorization': 'Bearer ' + access_token
	}, files =
	{
		'file': ('invalid.txt', 'invalid'.encode(), 'text/plain')
	})

	assert upload_response.status_code == 400


def test_get_assets(test_client : TestClient) -> None:
	get_response = test_client.get('/assets')

	assert get_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	get_response = test_client.get('/assets', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	get_body = get_response.json()

	assert get_body.get('assets') == []

	assert get_response.status_code == 200

	source_path = get_test_example_file('source.jpg')
	target_path = get_test_example_file('target-240p.mp4')

	with open(source_path, 'rb') as source_file, open(target_path, 'rb') as target_file:
		source_content = source_file.read()
		target_content = target_file.read()
		test_client.post('/assets?type=source', headers =
		{
			'Authorization': 'Bearer ' + access_token
		}, files =
		[
			('file', ('source.jpg', source_content, 'image/jpeg')),
			('file', ('target.mp4', target_content, 'video/mp4'))
		])

	get_response = test_client.get('/assets', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	get_body = get_response.json()
	assets = get_body.get('assets')

	assert len(assets) == 2
	assert assets[0].get('media') == 'image'
	assert assets[1].get('media') == 'video'

	assert get_response.status_code == 200


def test_get_asset(test_client : TestClient) -> None:
	get_response = test_client.get('invalid')

	assert get_response.status_code == 404

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	source_path = get_test_example_file('source.jpg')

	with open(source_path, 'rb') as source_file:
		source_content = source_file.read()
		upload_response = test_client.post('/assets?type=source', headers =
		{
			'Authorization': 'Bearer ' + access_token
		}, files =
		[
			('file', ('source.jpg', source_content, 'image/jpeg'))
		])
	upload_body = upload_response.json()
	asset_id = upload_body.get('asset_ids')[0]

	second_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	second_session_body = second_session_response.json()
	second_access_token = second_session_body.get('access_token')

	get_response = test_client.get('/assets/' + asset_id, headers =
	{
		'Authorization': 'Bearer ' + second_access_token
	})

	assert get_response.status_code == 404

	get_response = test_client.get('/assets/' + asset_id, headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	get_body = get_response.json()

	assert get_body.get('id') == asset_id
	assert get_body.get('type') == 'source'
	assert get_body.get('media') == 'image'
	assert get_body.get('format') == 'jpeg'
	assert get_body.get('metadata').get('resolution') == [ 1024, 1024 ]

	assert get_response.status_code == 200


def test_delete_assets(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')
	session_id = session_manager.find_session_id(access_token)

	source_path = get_test_example_file('source.jpg')

	with open(source_path, 'rb') as source_file:
		source_content = source_file.read()
		upload_response = test_client.post('/assets?type=source', headers =
		{
			'Authorization': 'Bearer ' + access_token
		}, files =
		[
			('file', ('source.jpg', source_content, 'image/jpeg'))
		])
	upload_body = upload_response.json()
	asset_id = upload_body.get('asset_ids')[0]

	assert asset_store.get_asset(session_id, asset_id)

	second_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	second_session_body = second_session_response.json()
	second_access_token = second_session_body.get('access_token')

	delete_response = test_client.request('DELETE', '/assets', headers =
	{
		'Authorization': 'Bearer ' + second_access_token
	}, json =
	{
		'asset_ids': [ asset_id ]
	})

	assert delete_response.status_code == 404

	delete_response = test_client.request('DELETE', '/assets', headers =
	{
		'Authorization': 'Bearer ' + access_token
	}, json =
	{
		'asset_ids': [ asset_id ]
	})

	assert delete_response.status_code == 200

	delete_response = test_client.request('DELETE', '/assets', headers =
	{
		'Authorization': 'Bearer ' + access_token
	}, json =
	{
		'asset_ids': [ asset_id ]
	})

	assert delete_response.status_code == 404
