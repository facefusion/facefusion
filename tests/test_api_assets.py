import subprocess
from typing import Iterator

import pytest
from starlette.testclient import TestClient

from facefusion import metadata, session_manager
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
	with TestClient(create_api()) as test_client:
		yield test_client


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	session_manager.SESSIONS.clear()
	asset_store.clear()


def test_upload_source_assets(test_client : TestClient) -> None:
	upload_response = test_client.post('/assets?type=source')

	assert upload_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	upload_response = test_client.post('/assets?type=source', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert upload_response.status_code == 400

	with open(get_test_example_file('source.jpg'), 'rb') as source_file:
		upload_response = test_client.post('/assets?type=source', files =
		{
			'file': ('source.jpg', source_file, 'image/jpeg')
		}, headers =
		{
			'Authorization': 'Bearer ' + access_token
		})
		upload_body = upload_response.json()

		assert upload_body.get('asset_ids')
		assert len(upload_body.get('asset_ids')) == 1
		assert upload_response.status_code == 201

	with open(get_test_example_file('source.jpg'), 'rb') as source_file_1:
		with open(get_test_example_file('source.jpg'), 'rb') as source_file_2:
			upload_response = test_client.post('/assets?type=source', files =
			[
				('file', ('source1.jpg', source_file_1, 'image/jpeg')),
				('file', ('source2.jpg', source_file_2, 'image/jpeg'))
			], headers =
			{
				'Authorization': 'Bearer ' + access_token
			})
			upload_body = upload_response.json()

			assert len(upload_body.get('asset_ids')) == 2
			assert upload_response.status_code == 201


def test_upload_target_asset(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	upload_response = test_client.post('/assets?type=target', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert upload_response.status_code == 400

	with open(get_test_example_file('target-240p.jpg'), 'rb') as target_file:
		upload_response = test_client.post('/assets?type=target', files =
		{
			'file': ('target.jpg', target_file, 'image/jpeg')
		}, headers =
		{
			'Authorization': 'Bearer ' + access_token
		})
		upload_body = upload_response.json()

		assert upload_body.get('asset_id')
		assert upload_response.status_code == 201

	with open(get_test_example_file('target-240p.jpg'), 'rb') as target_file_1:
		with open(get_test_example_file('target-240p.jpg'), 'rb') as target_file_2:
			upload_response = test_client.post('/assets?type=target', files =
			[
				('file', ('target1.jpg', target_file_1, 'image/jpeg')),
				('file', ('target2.jpg', target_file_2, 'image/jpeg'))
			], headers =
			{
				'Authorization': 'Bearer ' + access_token
			})

			assert upload_response.status_code == 400


def test_upload_invalid_type(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	with open(get_test_example_file('source.jpg'), 'rb') as source_file:
		upload_response = test_client.post('/assets?type=invalid', files =
		{
			'file': ('source.jpg', source_file, 'image/jpeg')
		}, headers =
		{
			'Authorization': 'Bearer ' + access_token
		})

		assert upload_response.status_code == 400


def test_list_assets(test_client : TestClient) -> None:
	list_response = test_client.get('/assets')

	assert list_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	list_response = test_client.get('/assets', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	list_body = list_response.json()

	assert list_body.get('assets') == []
	assert list_body.get('count') == 0
	assert list_response.status_code == 200

	with open(get_test_example_file('source.jpg'), 'rb') as source_file:
		test_client.post('/assets?type=source', files =
		{
			'file': ('source.jpg', source_file, 'image/jpeg')
		}, headers =
		{
			'Authorization': 'Bearer ' + access_token
		})

	with open(get_test_example_file('target-240p.mp4'), 'rb') as target_file:
		test_client.post('/assets?type=target', files =
		{
			'file': ('target.mp4', target_file, 'video/mp4')
		}, headers =
		{
			'Authorization': 'Bearer ' + access_token
		})

	list_response = test_client.get('/assets', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	list_body = list_response.json()

	assert list_body.get('count') == 2
	assert list_response.status_code == 200

	list_response = test_client.get('/assets?type=source', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	list_body = list_response.json()

	assert list_body.get('count') == 1
	assert list_body.get('assets')[0].get('type') == 'source'

	list_response = test_client.get('/assets?type=target', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	list_body = list_response.json()

	assert list_body.get('count') == 1
	assert list_body.get('assets')[0].get('type') == 'target'

	list_response = test_client.get('/assets?media=image', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	list_body = list_response.json()

	assert list_body.get('count') == 1
	assert list_body.get('assets')[0].get('media') == 'image'

	list_response = test_client.get('/assets?media=video', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	list_body = list_response.json()

	assert list_body.get('count') == 1
	assert list_body.get('assets')[0].get('media') == 'video'


def test_get_asset(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	get_response = test_client.get('/assets/invalid', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert get_response.status_code == 404

	with open(get_test_example_file('source.jpg'), 'rb') as source_file:
		upload_response = test_client.post('/assets?type=source', files =
		{
			'file': ('source.jpg', source_file, 'image/jpeg')
		}, headers =
		{
			'Authorization': 'Bearer ' + access_token
		})
		upload_body = upload_response.json()
		asset_id = upload_body.get('asset_ids')[0]

	get_response = test_client.get('/assets/' + asset_id, headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	get_body = get_response.json()

	assert get_body.get('id') == asset_id
	assert get_body.get('type') == 'source'
	assert get_body.get('media') == 'image'
	assert get_body.get('format') == 'jpeg'
	assert get_body.get('size') > 0
	assert get_body.get('created_at')
	assert get_body.get('expires_at')
	assert get_body.get('metadata')
	assert get_response.status_code == 200


def test_download_asset(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	with open(get_test_example_file('source.jpg'), 'rb') as source_file:
		original_content = source_file.read()
		source_file.seek(0)
		upload_response = test_client.post('/assets?type=source', files =
		{
			'file': ('source.jpg', source_file, 'image/jpeg')
		}, headers =
		{
			'Authorization': 'Bearer ' + access_token
		})
		upload_body = upload_response.json()
		asset_id = upload_body.get('asset_ids')[0]

	download_response = test_client.get('/assets/' + asset_id + '?action=download', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert download_response.status_code == 200
	assert len(download_response.content) == len(original_content)


def test_delete_asset(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	delete_response = test_client.delete('/assets/invalid', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert delete_response.status_code == 404

	with open(get_test_example_file('source.jpg'), 'rb') as source_file:
		upload_response = test_client.post('/assets?type=source', files =
		{
			'file': ('source.jpg', source_file, 'image/jpeg')
		}, headers =
		{
			'Authorization': 'Bearer ' + access_token
		})
		upload_body = upload_response.json()
		asset_id = upload_body.get('asset_ids')[0]

	delete_response = test_client.delete('/assets/' + asset_id, headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert delete_response.status_code == 200

	get_response = test_client.get('/assets/' + asset_id, headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert get_response.status_code == 404


def test_session_isolation(test_client : TestClient) -> None:
	create_session_response_1 = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	access_token_1 = create_session_response_1.json().get('access_token')

	create_session_response_2 = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	access_token_2 = create_session_response_2.json().get('access_token')

	with open(get_test_example_file('source.jpg'), 'rb') as source_file:
		upload_response = test_client.post('/assets?type=source', files =
		{
			'file': ('source.jpg', source_file, 'image/jpeg')
		}, headers =
		{
			'Authorization': 'Bearer ' + access_token_1
		})
		asset_id = upload_response.json().get('asset_ids')[0]

	list_response_1 = test_client.get('/assets', headers =
	{
		'Authorization': 'Bearer ' + access_token_1
	})

	assert list_response_1.json().get('count') == 1

	list_response_2 = test_client.get('/assets', headers =
	{
		'Authorization': 'Bearer ' + access_token_2
	})

	assert list_response_2.json().get('count') == 0

	get_response = test_client.get('/assets/' + asset_id, headers =
	{
		'Authorization': 'Bearer ' + access_token_2
	})

	assert get_response.status_code == 404
