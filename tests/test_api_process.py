import tempfile
from argparse import ArgumentParser
from typing import Iterator

import pytest
from starlette.testclient import TestClient

from facefusion import args_store, content_analyser, face_classifier, face_detector, face_landmarker, face_masker, face_recognizer, metadata, session_manager, state_manager, voice_extractor
from facefusion.apis import asset_store
from facefusion.apis.core import create_api
from facefusion.args_helper import apply_args
from facefusion.core import processors_pre_check
from facefusion.download import conditional_download
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
	state_manager.init_item('execution_thread_count', 1)
	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('video_memory_strategy', 'strict')
	state_manager.init_item('log_level', 'info')
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])
	state_manager.init_item('download_scope', 'lite')
	state_manager.init_item('source_paths', None)
	state_manager.init_item('processors', [ 'face_swapper' ])
	state_manager.init_item('face_selector_mode', 'many')

	args_store.register_argument_set(
	[
		ArgumentParser().add_argument('--source-paths', nargs = '+')
	], scopes = [ 'api' ])

	for module in [ content_analyser, face_classifier, face_detector, face_landmarker, face_masker, face_recognizer, voice_extractor ]:
		module.pre_check()

	processors_pre_check()

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
		result_bytes = websocket.receive_bytes()

	assert len(result_bytes) > 0
