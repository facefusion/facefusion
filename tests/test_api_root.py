from typing import Iterator

import pytest
from starlette.testclient import TestClient

from facefusion import metadata, session_manager
from facefusion.apis.core import create_api


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	session_manager.API_SESSIONS.clear()


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	with TestClient(create_api()) as test_client:
		yield test_client


def test_get_root(test_client : TestClient) -> None:
	get_root_response = test_client.get('/')
	get_root_body = get_root_response.json()

	assert get_root_body.get('name') == metadata.get('name')
	assert get_root_body.get('version') == metadata.get('version')
	assert get_root_response.status_code == 200
