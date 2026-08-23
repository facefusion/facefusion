from typing import Iterator
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from facefusion import metadata, session_manager
from facefusion.apis.core import create_api
from facefusion.jobs.job_manager import clear_jobs, find_job_ids, init_jobs
from .assert_helper import get_test_jobs_directory


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	session_manager.SESSIONS.clear()
	clear_jobs(get_test_jobs_directory())
	init_jobs(get_test_jobs_directory())


@pytest.fixture(scope = 'module')
def test_client() -> Iterator[TestClient]:
	with TestClient(create_api()) as test_client:
		yield test_client


def test_create_job(test_client : TestClient) -> None:
	create_job_response = test_client.post('/jobs')

	assert create_job_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	create_job_response = test_client.post('/jobs', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	create_job_body = create_job_response.json()

	assert create_job_body.get('job_id') in find_job_ids('drafted')
	assert create_job_response.status_code == 201

	with patch('facefusion.jobs.job_helper.suggest_job_id', return_value = 'job-test-create-job'):
		create_job_response = test_client.post('/jobs', headers =
		{
			'Authorization': 'Bearer ' + access_token
		})

		assert create_job_response.status_code == 201

		create_job_response = test_client.post('/jobs', headers =
		{
			'Authorization': 'Bearer ' + access_token
		})
		create_job_body = create_job_response.json()

		assert create_job_body.get('message') == 'job not created'
		assert create_job_response.status_code == 400
