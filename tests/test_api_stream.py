import asyncio
import tempfile
from typing import Iterator

import cv2
import numpy
import pytest
from starlette.testclient import TestClient

from facefusion import metadata, session_manager, state_manager
from facefusion.apis import asset_store
from facefusion.apis.core import create_api
from facefusion.core import common_pre_check, processors_pre_check
from facefusion.download import conditional_download
from .assert_helper import get_test_example_file, get_test_examples_directory
from .stream_helper import create_rtc_offer


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg'
	])


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])
	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('processors', [ 'face_swapper' ])
	state_manager.init_item('face_selector_mode', 'many')
	state_manager.init_item('face_detector_model', 'yolo_face')
	state_manager.init_item('face_detector_size', '640x640')
	state_manager.init_item('face_detector_score', 0.5)
	state_manager.init_item('face_detector_angles', [ 0 ])
	state_manager.init_item('face_detector_margin', [ 0, 0, 0, 0 ])
	state_manager.init_item('face_landmarker_model', '2dfan4')
	state_manager.init_item('face_landmarker_score', 0.5)
	state_manager.init_item('face_mask_types', [ 'box' ])
	state_manager.init_item('face_mask_blur', 0.3)
	state_manager.init_item('face_mask_padding', [ 0, 0, 0, 0 ])
	state_manager.init_item('face_swapper_model', 'hyperswap_1a_256')
	state_manager.init_item('face_swapper_pixel_boost', '256x256')
	state_manager.init_item('face_swapper_weight', 0.5)

	common_pre_check()
	processors_pre_check()

	with TestClient(create_api()) as test_client:
		yield test_client


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	state_manager.init_item('source_paths', None)
	session_manager.SESSIONS.clear()
	asset_store.clear()


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

	with test_client.websocket_connect('/stream', subprotocols =
	[
		'access_token.' + access_token
	]) as websocket:
		websocket.send_bytes(source_content)
		output_bytes = websocket.receive_bytes()
		output_vision_frame = cv2.imdecode(numpy.frombuffer(output_bytes, numpy.uint8), cv2.IMREAD_COLOR)

	assert output_vision_frame.shape == (1024, 1024, 3)


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

	rtc_offer = asyncio.run(create_rtc_offer())
	stream_response = test_client.post('/stream', json = rtc_offer, headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert stream_response.status_code == 200
	assert stream_response.json().get('type') == 'answer'
	assert stream_response.json().get('sdp')
