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


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	with TestClient(create_api()) as test_client:
		yield test_client


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
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
