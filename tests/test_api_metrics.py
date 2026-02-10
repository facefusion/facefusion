from typing import Iterator

import pytest
from pytest_mock import MockerFixture
from starlette.testclient import TestClient

from facefusion import metadata, session_manager
from facefusion.apis.core import create_api


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	with TestClient(create_api()) as test_client:
		yield test_client


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	session_manager.SESSIONS.clear()


@pytest.fixture(scope = 'function', autouse = True)
def mock_detect_execution_devices(mocker : MockerFixture) -> None:
	mocker.patch('facefusion.system.state_manager.get_temp_path', return_value = '/tmp')
	mocker.patch('facefusion.system.detect_disk_metrics', return_value =
	[
		{
			'total':
			{
				'value': 500,
				'unit': 'GB'
			},
			'free':
			{
				'value': 200,
				'unit': 'GB'
			},
			'utilization':
			{
				'value': 60,
				'unit': '%'
			}
		}
	])
	mocker.patch('facefusion.system.detect_memory_metrics', return_value =
	{
		'total':
		{
			'value': 32,
			'unit': 'GB'
		},
		'free':
		{
			'value': 16,
			'unit': 'GB'
		},
		'utilization':
		{
			'value': 50,
			'unit': '%'
		}
	})
	mocker.patch('facefusion.system.detect_execution_devices', return_value =
	[
		{
			'driver_version': '555.42',
			'framework':
			{
				'name': 'CUDA',
				'version': '12.5'
			},
			'product':
			{
				'vendor': 'NVIDIA',
				'name': 'RTX 4090'
			},
			'video_memory':
			{
				'total':
				{
					'value': 24,
				  	'unit': 'GB'
				},
				'free':
				{
					'value': 20,
					'unit': 'GB'
				}
			},
			'temperature':
			{
				'gpu':
				{
					'value': 45,
					'unit': 'C'
				},
				'memory':
				{
					'value': 0,
					'unit': 'C'
				}
			},
			'utilization':
			{
				'gpu':
				{
					'value': 30,
					'unit': '%'
				},
				'memory':
				{
					'value': 15,
					'unit': '%'
				}
			}
		}
	])


def test_get_metrics(test_client : TestClient) -> None:
	metrics_response = test_client.get('/metrics')

	assert metrics_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	metrics_response = test_client.get('/metrics', headers =
	{
		'Authorization': 'Bearer ' + create_session_body.get('access_token')
	})
	metrics_body = metrics_response.json()

	assert metrics_response.status_code == 200

	assert metrics_body.get('execution_devices')[0].get('driver_version') == '555.42'
	assert metrics_body.get('execution_devices')[0].get('product').get('name') == 'RTX 4090'
	assert metrics_body.get('execution_devices')[0].get('video_memory').get('total').get('value') == 24

	assert metrics_body.get('disks')[0].get('total').get('value') == 500
	assert metrics_body.get('disks')[0].get('free').get('unit') == 'GB'
	assert metrics_body.get('disks')[0].get('utilization').get('value') == 60

	assert metrics_body.get('memory').get('total').get('value') == 32
	assert metrics_body.get('memory').get('free').get('unit') == 'GB'
	assert metrics_body.get('memory').get('utilization').get('value') == 50


def test_websocket_metrics(test_client : TestClient) -> None:
	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()

	with test_client.websocket_connect('/metrics', subprotocols =
	[
		'access_token.' + create_session_body.get('access_token')
	]) as websocket:
		metrics_set = websocket.receive_json()

		assert metrics_set.get('execution_devices')[0].get('driver_version') == '555.42'
		assert metrics_set.get('execution_devices')[0].get('product').get('name') == 'RTX 4090'
		assert metrics_set.get('execution_devices')[0].get('video_memory').get('total').get('value') == 24

		assert metrics_set.get('disks')[0].get('total').get('value') == 500
		assert metrics_set.get('disks')[0].get('free').get('unit') == 'GB'
		assert metrics_set.get('disks')[0].get('utilization').get('value') == 60

		assert metrics_set.get('memory').get('total').get('value') == 32
		assert metrics_set.get('memory').get('free').get('unit') == 'GB'
		assert metrics_set.get('memory').get('utilization').get('value') == 50
