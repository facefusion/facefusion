from typing import Iterator
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from facefusion import metadata, session_manager
from facefusion.apis.core import create_api
from facefusion.jobs.job_manager import clear_jobs, create_job, find_job_ids, init_jobs
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


def test_get_jobs(test_client : TestClient) -> None:
	get_jobs_response = test_client.get('/jobs?status=drafted')

	assert get_jobs_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	get_jobs_response = test_client.get('/jobs?status=invalid', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	get_jobs_body = get_jobs_response.json()

	assert get_jobs_body.get('message') == 'invalid job status'
	assert get_jobs_response.status_code == 400

	create_job('job-test-get-jobs')

	get_jobs_response = test_client.get('/jobs?status=drafted', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	get_jobs_body = get_jobs_response.json()

	assert 'job-test-get-jobs' in get_jobs_body
	assert get_jobs_response.status_code == 200


def test_get_job(test_client : TestClient) -> None:
	get_job_response = test_client.get('/jobs/job-test-get-job')

	assert get_job_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	get_job_response = test_client.get('/jobs/job-test-unknown', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	get_job_body = get_job_response.json()

	assert get_job_body.get('message') == 'job not found'
	assert get_job_response.status_code == 404

	create_job('job-test-get-job')

	get_job_response = test_client.get('/jobs/job-test-get-job', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	get_job_body = get_job_response.json()

	assert get_job_body.get('version') == '1'
	assert get_job_response.status_code == 200


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


def test_delete_jobs(test_client : TestClient) -> None:
	delete_jobs_response = test_client.delete('/jobs')

	assert delete_jobs_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	delete_jobs_response = test_client.delete('/jobs', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	delete_jobs_body = delete_jobs_response.json()

	assert delete_jobs_body.get('message') == 'job not found'
	assert delete_jobs_response.status_code == 404

	create_job('job-test-delete-jobs-1')
	create_job('job-test-delete-jobs-2')

	delete_jobs_response = test_client.delete('/jobs', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert find_job_ids('drafted') == []
	assert delete_jobs_response.status_code == 200


def test_delete_job(test_client : TestClient) -> None:
	delete_job_response = test_client.delete('/jobs/job-test-delete-job')

	assert delete_job_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	delete_job_response = test_client.delete('/jobs/job-test-unknown', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	delete_job_body = delete_job_response.json()

	assert delete_job_body.get('message') == 'job not found'
	assert delete_job_response.status_code == 404

	create_job('job-test-delete-job')

	delete_job_response = test_client.delete('/jobs/job-test-delete-job', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert find_job_ids('drafted') == []
	assert delete_job_response.status_code == 200
