from typing import Iterator
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from facefusion import metadata, session_manager
from facefusion.apis.core import create_api
from facefusion.jobs.job_manager import clear_jobs, count_step_total, create_job, find_job_ids, init_jobs
from facefusion.program import create_program
from .assert_helper import get_test_jobs_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	create_program()


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


def test_submit_jobs(test_client : TestClient) -> None:
	submit_jobs_response = test_client.patch('/jobs?action=submit')

	assert submit_jobs_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	submit_jobs_response = test_client.patch('/jobs?action=invalid', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	submit_jobs_body = submit_jobs_response.json()

	assert submit_jobs_body.get('message') == 'invalid job action'
	assert submit_jobs_response.status_code == 400

	create_job('job-test-submit-jobs')

	submit_jobs_response = test_client.patch('/jobs?action=submit', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	submit_jobs_body = submit_jobs_response.json()

	assert submit_jobs_body.get('message') == 'jobs not submitted'
	assert submit_jobs_response.status_code == 400

	with patch('facefusion.jobs.job_manager.submit_jobs', return_value = True):
		submit_jobs_response = test_client.patch('/jobs?action=submit', headers =
		{
			'Authorization': 'Bearer ' + access_token
		})
		submit_jobs_body = submit_jobs_response.json()

		assert submit_jobs_body.get('message') == 'ok'
		assert submit_jobs_response.status_code == 200


def test_submit_job(test_client : TestClient) -> None:
	submit_job_response = test_client.patch('/jobs/job-test-submit-job?action=submit')

	assert submit_job_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	submit_job_response = test_client.patch('/jobs/job-test-submit-job?action=invalid', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	submit_job_body = submit_job_response.json()

	assert submit_job_body.get('message') == 'invalid job action'
	assert submit_job_response.status_code == 400

	create_job('job-test-submit-job')

	submit_job_response = test_client.patch('/jobs/job-test-submit-job?action=submit', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	submit_job_body = submit_job_response.json()

	assert submit_job_body.get('message') == 'job not submitted'
	assert submit_job_response.status_code == 400

	with patch('facefusion.jobs.job_manager.submit_job', return_value = True):
		submit_job_response = test_client.patch('/jobs/job-test-submit-job?action=submit', headers =
		{
			'Authorization': 'Bearer ' + access_token
		})
		submit_job_body = submit_job_response.json()

		assert submit_job_body.get('message') == 'ok'
		assert submit_job_response.status_code == 200


def test_run_jobs(test_client : TestClient) -> None:
	run_jobs_response = test_client.patch('/jobs?action=run')

	assert run_jobs_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	run_jobs_response = test_client.patch('/jobs?action=run', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	run_jobs_body = run_jobs_response.json()

	assert run_jobs_body.get('message') == 'jobs not run'
	assert run_jobs_response.status_code == 400

	with patch('facefusion.jobs.job_manager.find_job_ids', return_value = [ 'job-test-run-jobs' ]):
		with patch('facefusion.jobs.job_runner.run_jobs', return_value = True) as run_jobs_mock:
			run_jobs_response = test_client.patch('/jobs?action=run', headers =
			{
				'Authorization': 'Bearer ' + access_token
			})
			run_jobs_body = run_jobs_response.json()

			assert run_jobs_body.get('message') == 'ok'
			assert run_jobs_response.status_code == 202
			assert run_jobs_mock.called is True


def test_run_job(test_client : TestClient) -> None:
	run_job_response = test_client.patch('/jobs/job-test-run-job?action=run')

	assert run_job_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	create_job('job-test-run-job')

	run_job_response = test_client.patch('/jobs/job-test-run-job?action=run', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	run_job_body = run_job_response.json()

	assert run_job_body.get('message') == 'job not run'
	assert run_job_response.status_code == 400

	with patch('facefusion.jobs.job_manager.find_job_ids', return_value = [ 'job-test-run-job' ]):
		with patch('facefusion.jobs.job_runner.run_job', return_value = True) as run_job_mock:
			run_job_response = test_client.patch('/jobs/job-test-run-job?action=run', headers =
			{
				'Authorization': 'Bearer ' + access_token
			})
			run_job_body = run_job_response.json()

			assert run_job_body.get('message') == 'ok'
			assert run_job_response.status_code == 202
			assert run_job_mock.called is True


def test_retry_jobs(test_client : TestClient) -> None:
	retry_jobs_response = test_client.patch('/jobs?action=retry')

	assert retry_jobs_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	retry_jobs_response = test_client.patch('/jobs?action=retry', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	retry_jobs_body = retry_jobs_response.json()

	assert retry_jobs_body.get('message') == 'jobs not retried'
	assert retry_jobs_response.status_code == 400

	with patch('facefusion.jobs.job_manager.find_job_ids', return_value = [ 'job-test-retry-jobs' ]):
		with patch('facefusion.jobs.job_runner.retry_jobs', return_value = True) as retry_jobs_mock:
			retry_jobs_response = test_client.patch('/jobs?action=retry', headers =
			{
				'Authorization': 'Bearer ' + access_token
			})
			retry_jobs_body = retry_jobs_response.json()

			assert retry_jobs_body.get('message') == 'ok'
			assert retry_jobs_response.status_code == 202
			assert retry_jobs_mock.called is True


def test_retry_job(test_client : TestClient) -> None:
	retry_job_response = test_client.patch('/jobs/job-test-retry-job?action=retry')

	assert retry_job_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	retry_job_response = test_client.patch('/jobs/job-test-retry-job?action=retry', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	retry_job_body = retry_job_response.json()

	assert retry_job_body.get('message') == 'job not retried'
	assert retry_job_response.status_code == 400

	with patch('facefusion.jobs.job_manager.find_job_ids', return_value = [ 'job-test-retry-job' ]):
		with patch('facefusion.jobs.job_runner.retry_job', return_value = True) as retry_job_mock:
			retry_job_response = test_client.patch('/jobs/job-test-retry-job?action=retry', headers =
			{
				'Authorization': 'Bearer ' + access_token
			})
			retry_job_body = retry_job_response.json()

			assert retry_job_body.get('message') == 'ok'
			assert retry_job_response.status_code == 202
			assert retry_job_mock.called is True


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

	assert delete_jobs_body.get('message') == 'jobs not deleted'
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

	assert delete_job_body.get('message') == 'job not deleted'
	assert delete_job_response.status_code == 404

	create_job('job-test-delete-job')

	delete_job_response = test_client.delete('/jobs/job-test-delete-job', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert find_job_ids('drafted') == []
	assert delete_job_response.status_code == 200


def test_create_step(test_client : TestClient) -> None:
	create_step_response = test_client.post('/jobs/job-test-create-step?action=add', json =
	{
		'processors': [ 'face_swapper' ]
	})

	assert create_step_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	create_job('job-test-create-step')

	create_step_response = test_client.post('/jobs/job-test-create-step?action=add', headers =
	{
		'Authorization': 'Bearer ' + access_token
	}, json =
	{
		'processors': [ 'face_swapper' ]
	})
	create_step_body = create_step_response.json()

	assert create_step_body.get('message') == 'ok'
	assert count_step_total('job-test-create-step') == 1
	assert create_step_response.status_code == 201

	get_job_response = test_client.get('/jobs/job-test-create-step', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	get_job_body = get_job_response.json()

	assert get_job_body.get('steps')[0].get('args') == { 'processors': [ 'face_swapper' ] }

	create_step_response = test_client.post('/jobs/job-test-create-step/0?action=insert', headers =
	{
		'Authorization': 'Bearer ' + access_token
	}, json =
	{
		'processors': [ 'face_swapper' ]
	})

	assert count_step_total('job-test-create-step') == 2
	assert create_step_response.status_code == 201

	create_step_response = test_client.post('/jobs/job-test-create-step/0?action=remix', headers =
	{
		'Authorization': 'Bearer ' + access_token
	}, json =
	{
		'processors': [ 'face_swapper' ]
	})

	assert count_step_total('job-test-create-step') == 3
	assert create_step_response.status_code == 201

	create_step_response = test_client.post('/jobs/job-test-create-step?action=invalid', headers =
	{
		'Authorization': 'Bearer ' + access_token
	}, json =
	{
		'processors': [ 'face_swapper' ]
	})
	create_step_body = create_step_response.json()

	assert create_step_body.get('message') == 'invalid job action'
	assert create_step_response.status_code == 400


def test_delete_step(test_client : TestClient) -> None:
	delete_step_response = test_client.delete('/jobs/job-test-delete-step/0')

	assert delete_step_response.status_code == 401

	create_session_response = test_client.post('/session', json =
	{
		'client_version': metadata.get('version')
	})
	create_session_body = create_session_response.json()
	access_token = create_session_body.get('access_token')

	create_job('job-test-delete-step')

	delete_step_response = test_client.delete('/jobs/job-test-delete-step/0', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})
	delete_step_body = delete_step_response.json()

	assert delete_step_body.get('message') == 'step not removed'
	assert delete_step_response.status_code == 404

	test_client.post('/jobs/job-test-delete-step?action=add', headers =
	{
		'Authorization': 'Bearer ' + access_token
	}, json =
	{
		'processors': [ 'face_swapper' ]
	})

	delete_step_response = test_client.delete('/jobs/job-test-delete-step/0', headers =
	{
		'Authorization': 'Bearer ' + access_token
	})

	assert count_step_total('job-test-delete-step') == 0
	assert delete_step_response.status_code == 200
