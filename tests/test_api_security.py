from typing import Iterator

import pytest
from starlette.testclient import TestClient

from facefusion import session_manager, state_manager
from facefusion.apis.core import create_api
from .assert_helper import get_test_jobs_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('jobs_path', get_test_jobs_directory())
	state_manager.init_item('api_session_limit', 10)


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	session_manager.API_SESSIONS.clear()


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	with TestClient(create_api()) as test_client:
		yield test_client


def test_create_security_guard(test_client : TestClient) -> None:
	get_root_response = test_client.get('/')

	assert get_root_response.headers.get('X-Content-Type-Options') == 'nosniff'
	assert get_root_response.headers.get('X-Frame-Options') == 'DENY'
	assert get_root_response.headers.get('Content-Security-Policy') == 'frame-ancestors \'none\''
	assert get_root_response.headers.get('Referrer-Policy') == 'no-referrer'
	assert get_root_response.headers.get('Cache-Control') == 'no-store'
	assert get_root_response.status_code == 200

	get_session_response = test_client.get('/session')

	assert get_session_response.headers.get('X-Content-Type-Options') == 'nosniff'
	assert get_session_response.headers.get('X-Frame-Options') == 'DENY'
	assert get_session_response.headers.get('Cache-Control') == 'no-store'
	assert get_session_response.status_code == 401

	create_session_response = test_client.post('/session', content = 'invalid')

	assert create_session_response.headers.get('X-Content-Type-Options') == 'nosniff'
	assert create_session_response.headers.get('Cache-Control') == 'no-store'
	assert create_session_response.status_code == 400
