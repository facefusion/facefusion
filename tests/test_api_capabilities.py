from argparse import ArgumentParser
from typing import Iterator

import pytest
from starlette.testclient import TestClient

from facefusion import args_store, session_manager
from facefusion.apis.core import create_api


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	program = ArgumentParser()
	args_store.register_arguments(
		[
			program.add_argument(
				'--source-paths',
				nargs = '+'
			)
		],
		scopes = [ 'api' ]
	)
	args_store.register_arguments(
		[
			program.add_argument(
				'--output-format',
				default = 'mp4',
				choices = [ 'mp4', 'mkv', 'webm' ]
			)
		],
		scopes = [ 'api' ]
	)

	with TestClient(create_api()) as test_client:
		yield test_client


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	session_manager.SESSIONS.clear()


def test_get_capabilities(test_client : TestClient) -> None:
	capabilities_response = test_client.get('/capabilities')
	capabilities_body = capabilities_response.json()

	assert capabilities_response.status_code == 200

	assert 'mp3' in capabilities_body.get('formats').get('audio')

	assert 'jpeg' in capabilities_body.get('formats').get('image')

	assert 'mp4' in capabilities_body.get('formats').get('video')

	assert capabilities_body.get('arguments').get('source_paths').get('default') is None
	assert capabilities_body.get('arguments').get('output_format').get('choices') == [ 'mp4', 'mkv', 'webm' ]
