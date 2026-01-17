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


def test_upload_asset_without_auth(test_client : TestClient) -> None:
	upload_response = test_client.post('/assets?type=source')

	assert upload_response.status_code == 401


def test_upload_asset_invalid_type(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	upload_response = test_client.post('/assets?type=invalid', headers =
	{
		'Authorization': 'Bearer ' + create_session_body.get('access_token')
	})

	assert upload_response.status_code == 400


def test_upload_asset_no_file(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	upload_response = test_client.post('/assets?type=source', headers =
	{
		'Authorization': 'Bearer ' + create_session_body.get('access_token')
	})

	assert upload_response.status_code == 400


def test_upload_source_asset(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	with open(get_test_example_file('source.jpg'), 'rb') as source_file:
		upload_response = test_client.post('/assets?type=source', headers =
		{
			'Authorization': 'Bearer ' + create_session_body.get('access_token')
		}, files =
		{
			'file': ('source.jpg', source_file, 'image/jpeg')
		})

	assert upload_response.status_code == 201
	assert upload_response.json().get('asset_ids')
	assert len(upload_response.json().get('asset_ids')) == 1


def test_upload_multiple_source_assets(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	with open(get_test_example_file('source.jpg'), 'rb') as source_file:
		source_content = source_file.read()
		upload_response = test_client.post('/assets?type=source', headers =
		{
			'Authorization': 'Bearer ' + create_session_body.get('access_token')
		}, files =
		[
			('file', ('source1.jpg', source_content, 'image/jpeg')),
			('file', ('source2.jpg', source_content, 'image/jpeg'))
		])

	assert upload_response.status_code == 201
	assert upload_response.json().get('asset_ids')
	assert len(upload_response.json().get('asset_ids')) == 2


def test_upload_target_asset(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	with open(get_test_example_file('target-240p.mp4'), 'rb') as target_file:
		upload_response = test_client.post('/assets?type=target', headers =
		{
			'Authorization': 'Bearer ' + create_session_body.get('access_token')
		}, files =
		{
			'file': ('target.mp4', target_file, 'video/mp4')
		})

	assert upload_response.status_code == 201
	assert upload_response.json().get('asset_id')


def test_upload_unsupported_format(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	upload_response = test_client.post('/assets?type=source', headers =
	{
		'Authorization': 'Bearer ' + create_session_body.get('access_token')
	}, files =
	{
		'file': ('test.txt', b'invalid content', 'text/plain')
	})

	assert upload_response.status_code == 400
