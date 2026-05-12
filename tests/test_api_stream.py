import tempfile
import threading
from typing import Iterator

import pytest
from starlette.testclient import TestClient

from facefusion import metadata, session_manager, state_manager
from facefusion.apis import asset_store
from facefusion.apis.core import create_api
from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.core import common_pre_check
from facefusion.download import conditional_download
from facefusion.hash_helper import create_hash
from .assert_helper import get_test_example_file, get_test_examples_directory
from .stream_helper import create_sdp_offer, open_websocket_stream


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])
	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('processors', [])

	common_pre_check()

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg'
	])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	session_manager.SESSIONS.clear()
	asset_store.clear()


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	with TestClient(create_api()) as test_client:
		yield test_client


def test_stream_image(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	access_token = create_session_response.json().get('access_token')
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

	asset_id = upload_response.json().get('asset_ids')[0]

	select_response = test_client.put('/state?action=select&type=source', json =
	{
		'asset_ids': [ asset_id ]
	}, headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert select_response.status_code == 200

	with test_client.websocket_connect('/stream?mode=image', subprotocols =
	[
		'access_token.' + access_token
	]) as websocket:
		websocket.send_bytes(source_content)
		output_buffer = websocket.receive_bytes()

	if is_linux() or is_windows():
		assert create_hash(output_buffer) == '0142782f'

	if is_macos():
		assert create_hash(output_buffer) == '0142782f'


def test_stream_video(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	access_token = create_session_response.json().get('access_token')
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

	asset_id = upload_response.json().get('asset_ids')[0]

	test_client.put('/state?action=select&type=source', json =
	{
		'asset_ids': [ asset_id ]
	}, headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	ready_event = threading.Event()
	stop_event = threading.Event()
	#TODO: use asyncio
	stream_thread = threading.Thread(target = open_websocket_stream, args = (test_client, [ 'access_token.' + access_token ], source_content, ready_event, stop_event))
	stream_thread.start()
	ready_event.wait(timeout = 10)

	assert ready_event.is_set()

	sdp_offer = create_sdp_offer()
	stream_response = test_client.post('/stream', content = sdp_offer, headers =
	{
		'Authorization': 'Bearer ' + access_token,
		'Content-Type': 'application/sdp'
	})

	# TODO: can we test if bytes have been passed? what does this actual test than just the handshake?
	assert stream_response.status_code == 201
	assert stream_response.text

	stop_event.set()
	stream_thread.join(timeout = 10)
