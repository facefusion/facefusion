import os

from facefusion.jobs.job_helper import get_step_output_path, suggest_job_id


def test_get_step_output_path() -> None:
	assert get_step_output_path('test-job', 0, 'test.mp4') == 'test-test-job-0.mp4'
	assert get_step_output_path('test-job', 0, 'test/test.mp4') == os.path.join('test', 'test-test-job-0.mp4')
	assert get_step_output_path('test-job', 0, 'invalid') is None


def test_suggest_job_id() -> None:
	job_id_1 = suggest_job_id()
	job_id_2 = suggest_job_id()

	assert job_id_1.startswith('job')
	assert not job_id_1 == job_id_2
