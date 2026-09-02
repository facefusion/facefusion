import os
import tempfile
from typing import Iterator

import pytest
from starlette.testclient import TestClient

from facefusion import ffmpeg, ffmpeg_builder, metadata, process_manager, session_manager, state_manager
from facefusion.apis import asset_store
from facefusion.apis.core import create_api
from facefusion.download import conditional_download
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])

	ffmpeg.run_ffmpeg(
		ffmpeg_builder.chain(
			ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
			[
				'-vframes',
				'1'
			],
			ffmpeg_builder.set_output(get_test_example_file('target-240p.jpg'))
		)
	)


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('temp_frame_format', 'png')
	session_manager.SESSIONS.clear()
	asset_store.clear()


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	with TestClient(create_api()) as test_client:
		yield test_client


def test_upload_asset(test_client : TestClient) -> None:
	upload_response = test_client.post('/assets?type=source')

	assert upload_response.status_code == 401

	source_path = get_test_example_file('source.jpg')
	target_image_path = get_test_example_file('target-240p.jpg')
	target_video_path = get_test_example_file('target-240p.mp4')
	audio_path = get_test_example_file('source.mp3')

	for security_strategy in [ 'strict', 'moderate' ]:
		state_manager.init_item('api_security_strategy', security_strategy)

		create_session_response = test_client.post('/session', json =
		{
			'client_version': metadata.get('version')
		})
		create_session_body = create_session_response.json()
		access_token = create_session_body.get('access_token')
		session_id = session_manager.find_session_id(access_token)

		with open(source_path, 'rb') as source_file:
			upload_response = test_client.post('/assets?type=source', headers =
			{
				'Authorization': 'Bearer ' + access_token
			}, files =
			[
				('file', ('source.jpg', source_file.read(), 'image/jpeg'))
			])
		asset_ids = upload_response.json().get('asset_ids')
		asset = asset_store.get_asset(session_id, asset_ids[0])

		assert asset.get('media') == 'image'
		assert asset.get('type') == 'source'
		assert asset.get('format') == 'jpeg'
		assert upload_response.status_code == 201

		with open(target_image_path, 'rb') as target_image_file, open(target_video_path, 'rb') as target_video_file:
			upload_response = test_client.post('/assets?type=target', headers =
			{
				'Authorization': 'Bearer ' + access_token
			}, files =
			[
				('file', ('target-240p.jpg', target_image_file.read(), 'image/jpeg')),
				('file', ('target-240p.mp4', target_video_file.read(), 'video/mp4'))
			])
		asset_ids = upload_response.json().get('asset_ids')

		assert asset_store.get_asset(session_id, asset_ids[0]).get('media') == 'image'
		assert asset_store.get_asset(session_id, asset_ids[0]).get('type') == 'target'
		assert asset_store.get_asset(session_id, asset_ids[0]).get('format') == 'jpeg'
		assert asset_store.get_asset(session_id, asset_ids[1]).get('media') == 'video'
		assert asset_store.get_asset(session_id, asset_ids[1]).get('type') == 'target'
		assert asset_store.get_asset(session_id, asset_ids[1]).get('format') == 'mp4'
		assert upload_response.status_code == 201

		with open(audio_path, 'rb') as audio_file:
			upload_response = test_client.post('/assets?type=source', headers =
			{
				'Authorization': 'Bearer ' + access_token
			}, files =
			[
				('file', ('source.mp3', audio_file.read(), 'audio/mpeg'))
			])
		asset_ids = upload_response.json().get('asset_ids')
		asset = asset_store.get_asset(session_id, asset_ids[0])

		assert asset.get('media') == 'audio'
		assert asset.get('type') == 'source'
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

		assert upload_response.status_code == 415

	state_manager.init_item('api_security_strategy', 'strict')


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
	target_image_path = get_test_example_file('target-240p.jpg')
	target_video_path = get_test_example_file('target-240p.mp4')

	with open(source_path, 'rb') as source_file:
		test_client.post('/assets?type=source', headers =
		{
			'Authorization': 'Bearer ' + access_token
		}, files =
		[
			('file', ('source.jpg', source_file.read(), 'image/jpeg'))
		])

	with open(target_image_path, 'rb') as target_image_file, open(target_video_path, 'rb') as target_video_file:
		test_client.post('/assets?type=target', headers =
		{
			'Authorization': 'Bearer ' + access_token
		}, files =
		[
			('file', ('target-240p.jpg', target_image_file.read(), 'image/jpeg')),
			('file', ('target-240p.mp4', target_video_file.read(), 'video/mp4'))
		])

	get_response = test_client.get('/assets', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	get_body = get_response.json()
	assets = get_body.get('assets')

	assert len(assets) == 3
	assert assets[0].get('media') == 'image'
	assert assets[1].get('media') == 'image'
	assert assets[2].get('media') == 'video'

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
		upload_response = test_client.post('/assets?type=source', headers =
		{
			'Authorization': 'Bearer ' + access_token
		}, files =
		[
			('file', ('source.jpg', source_file.read(), 'image/jpeg'))
		])
	asset_ids = upload_response.json().get('asset_ids')

	second_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	second_session_body = second_session_response.json()
	second_access_token = second_session_body.get('access_token')

	get_response = test_client.get('/assets/' + asset_ids[0], headers =
	{
		'Authorization': 'Bearer ' + second_access_token
	})

	assert get_response.status_code == 404

	get_response = test_client.get('/assets/' + asset_ids[0], headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	get_body = get_response.json()

	assert get_body.get('id') == asset_ids[0]
	assert get_body.get('type') == 'source'
	assert get_body.get('media') == 'image'
	assert get_body.get('format') == 'jpeg'
	assert get_body.get('metadata').get('resolution') == [ 1024, 1024 ]

	assert get_response.status_code == 200


def test_delete_asset(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')
	session_id = session_manager.find_session_id(access_token)

	source_path = get_test_example_file('source.jpg')

	with open(source_path, 'rb') as source_file:
		upload_response = test_client.post('/assets?type=source', headers =
		{
			'Authorization': 'Bearer ' + access_token
		}, files =
		[
			('file', ('source.jpg', source_file.read(), 'image/jpeg'))
		])
	asset_ids = upload_response.json().get('asset_ids')
	asset_path = asset_store.get_asset(session_id, asset_ids[0]).get('path')

	assert os.path.exists(asset_path) is True

	second_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	second_session_body = second_session_response.json()
	second_access_token = second_session_body.get('access_token')

	delete_response = test_client.request('DELETE', '/assets/' + asset_ids[0], headers =
	{
		'Authorization': 'Bearer ' + second_access_token
	})

	assert delete_response.status_code == 404
	assert os.path.exists(asset_path) is True

	delete_response = test_client.request('DELETE', '/assets/' + asset_ids[0], headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert delete_response.status_code == 200
	assert os.path.exists(asset_path) is False
	assert asset_store.get_asset(session_id, asset_ids[0]) is None

	delete_response = test_client.request('DELETE', '/assets/' + asset_ids[0], headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert delete_response.status_code == 404


def test_delete_assets(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')
	session_id = session_manager.find_session_id(access_token)

	source_path = get_test_example_file('source.jpg')
	target_image_path = get_test_example_file('target-240p.jpg')
	target_video_path = get_test_example_file('target-240p.mp4')

	with open(source_path, 'rb') as source_file:
		test_client.post('/assets?type=source', headers =
		{
			'Authorization': 'Bearer ' + access_token
		}, files =
		[
			('file', ('source.jpg', source_file.read(), 'image/jpeg'))
		])

	with open(target_image_path, 'rb') as target_image_file, open(target_video_path, 'rb') as target_video_file:
		test_client.post('/assets?type=target', headers =
		{
			'Authorization': 'Bearer ' + access_token
		}, files =
		[
			('file', ('target-240p.jpg', target_image_file.read(), 'image/jpeg')),
			('file', ('target-240p.mp4', target_video_file.read(), 'video/mp4'))
		])
	asset_paths = []

	for asset in asset_store.get_assets(session_id).values():
		asset_paths.append(asset.get('path'))

	for asset_path in asset_paths:
		assert os.path.exists(asset_path) is True

	second_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	second_session_body = second_session_response.json()
	second_access_token = second_session_body.get('access_token')

	delete_response = test_client.request('DELETE', '/assets', headers =
	{
		'Authorization': 'Bearer ' + second_access_token
	})

	assert delete_response.status_code == 200

	for asset_path in asset_paths:
		assert os.path.exists(asset_path) is True

	delete_response = test_client.request('DELETE', '/assets', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert delete_response.status_code == 200
	assert asset_store.get_assets(session_id) is None

	for asset_path in asset_paths:
		assert os.path.exists(asset_path) is False
