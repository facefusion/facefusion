from typing import Iterator

import pytest
from starlette.testclient import TestClient

from facefusion.apis.core import create_api


@pytest.fixture(scope='module')
def test_client() -> Iterator[TestClient]:
    with TestClient(create_api()) as test_client:
        yield test_client


@pytest.fixture(scope='function', autouse=True)
def before_each() -> None:
    from facefusion import session_manager
    session_manager.SESSIONS.clear()


@pytest.fixture(scope='function')
def access_token(test_client: TestClient, before_each) -> str:
    response = test_client.post('/session', json={'api_key': ''})
    assert response.status_code == 201
    return response.json()['access_token']


def test_websocket_ping_connection(test_client: TestClient, access_token: str) -> None:
    with test_client.websocket_connect('/ping', subprotocols=[f'access_token.{access_token}']) as websocket:
        assert websocket

