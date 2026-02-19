import shutil
import tempfile
from typing import Iterator
from unittest.mock import patch

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
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg'
	])


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	with TestClient(create_api()) as test_client:
		yield test_client


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('temp_frame_format', 'png')
	state_manager.init_item('source_paths', None)
	session_manager.SESSIONS.clear()
	asset_store.clear()


def mock_process_image(start_time : float) -> int:
	output_path = state_manager.get_item('output_path')
	target_path = state_manager.get_item('target_path')
	shutil.copy(target_path, output_path)
	return 0


def test_websocket_process_image_without_auth(test_client : TestClient) -> None:
	with pytest.raises(Exception):
		with test_client.websocket_connect('/process/image') as _:
			pass


def test_websocket_process_image_without_source(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	access_token = create_session_response.json().get('access_token')

	with test_client.websocket_connect('/process/image', subprotocols =
	[
		'access_token.' + access_token
	]) as websocket:
		with pytest.raises(Exception):
			websocket.receive_bytes()


def test_websocket_process_image_single(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	access_token = create_session_response.json().get('access_token')
	source_path = get_test_example_file('source.jpg')
	state_manager.init_item('source_paths', [ source_path ])

	with open(source_path, 'rb') as source_file:
		image_bytes = source_file.read()

	with patch('facefusion.apis.endpoints.process.image_to_image.process', side_effect = mock_process_image):
		with test_client.websocket_connect('/process/image', subprotocols =
		[
			'access_token.' + access_token
		]) as websocket:
			websocket.send_bytes(image_bytes)
			result_bytes = websocket.receive_bytes()

	assert len(result_bytes) > 0


def test_websocket_process_image_batch(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	access_token = create_session_response.json().get('access_token')
	source_path = get_test_example_file('source.jpg')
	state_manager.init_item('source_paths', [ source_path ])

	with open(source_path, 'rb') as source_file:
		image_bytes = source_file.read()

	with patch('facefusion.apis.endpoints.process.image_to_image.process', side_effect = mock_process_image):
		with test_client.websocket_connect('/process/image', subprotocols =
		[
			'access_token.' + access_token
		]) as websocket:
			websocket.send_bytes(image_bytes)
			result_bytes_1 = websocket.receive_bytes()
			websocket.send_bytes(image_bytes)
			result_bytes_2 = websocket.receive_bytes()

	assert len(result_bytes_1) > 0
	assert len(result_bytes_2) > 0
