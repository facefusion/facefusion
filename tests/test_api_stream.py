import tempfile
import threading
from functools import partial
from typing import Iterator
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from facefusion import metadata, rtc, rtc_store, session_manager, state_manager
from facefusion.apis import asset_store
from facefusion.apis.core import create_api
from facefusion.core import common_pre_check
from facefusion.download import conditional_download
from facefusion.hash_helper import create_hash
from facefusion.libraries import datachannel as datachannel_module
from .assert_helper import get_test_example_file, get_test_examples_directory


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
	rtc_store.clear()


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	with TestClient(create_api()) as test_client:
		yield test_client


@pytest.fixture(scope = 'function')
def create_event() -> threading.Event:
	return threading.Event()


@pytest.mark.helper
def set_event(rtc_peer, video_buffer : bytes, video_timestamp : int, event : threading.Event) -> None:
	event.set()


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

	with test_client.websocket_connect('/stream?type=image&action=process', subprotocols =
	[
		'access_token.' + access_token
	]) as websocket:
		websocket.send_bytes(source_content)
		output_buffer = websocket.receive_bytes()

	assert create_hash(output_buffer) == '0142782f'


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8' ])
def test_stream_video(test_client : TestClient, create_event : threading.Event, video_codec : str) -> None:
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

	peer_connection = rtc.create_peer_connection()
	video_payload_type = 96 if video_codec == 'vp8' else 35
	rtc.add_video_track(peer_connection, 'sendrecv', video_codec, video_payload_type)
	rtc.add_audio_track(peer_connection, 'sendrecv', 'opus', 111)
	sdp_offer = rtc.create_sdp_offer(peer_connection)
	datachannel_module.create_static_library().rtcDeletePeerConnection(peer_connection)

	with patch('facefusion.rtc.send_video', side_effect = partial(set_event, event = create_event)):
		stream_response = test_client.post('/stream?type=video&action=process', content = sdp_offer, headers =
		{
			'Authorization': 'Bearer ' + access_token,
			'Content-Type': 'application/sdp'
		})

		assert stream_response.status_code == 201
		assert 'm=video' in stream_response.text
