import tempfile
from typing import Iterator

import cv2
import numpy
import pytest
from starlette.testclient import TestClient

from facefusion import face_classifier, face_detector, face_landmarker, face_masker, face_recognizer, metadata, session_manager, state_manager
from facefusion.apis import asset_store
from facefusion.apis.core import create_api
from facefusion.args_helper import apply_args
from facefusion.download import conditional_download
from facefusion.processors.core import get_processors_modules
from facefusion.program import collect_step_program
from .helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg'
	])


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	state_manager.init_item('config_path', 'facefusion.ini')
	program = collect_step_program()
	args = vars(program.parse_args([]))
	apply_args(args, state_manager.init_item)
	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])
	state_manager.init_item('face_selector_mode', 'many')
	face_classifier.pre_check()
	face_detector.pre_check()
	face_landmarker.pre_check()
	face_masker.pre_check()
	face_recognizer.pre_check()

	for processor_module in get_processors_modules(state_manager.get_item('processors')):
		processor_module.pre_check()

	with TestClient(create_api()) as test_client:
		yield test_client


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	state_manager.init_item('source_paths', None)
	session_manager.SESSIONS.clear()
	asset_store.clear()


def test_process_image(test_client : TestClient) -> None:
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

	with test_client.websocket_connect('/process/image', subprotocols =
	[
		'access_token.' + access_token
	]) as websocket:
		websocket.send_bytes(source_content)
		output_bytes = websocket.receive_bytes()
		output_vision_frame = cv2.imdecode(numpy.frombuffer(output_bytes, numpy.uint8), cv2.IMREAD_COLOR)

	assert output_vision_frame.shape == (1024, 1024, 3)
