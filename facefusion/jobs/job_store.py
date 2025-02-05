from typing import List

from facefusion.types import JobStore

JOB_STORE : JobStore =\
{
	'job_keys': [],
	'step_keys': []
}


def get_job_keys() -> List[str]:
	return JOB_STORE.get('job_keys')


def get_step_keys() -> List[str]:
	return JOB_STORE.get('step_keys')


def register_job_keys(step_keys : List[str]) -> None:
	for step_key in step_keys:
		JOB_STORE['job_keys'].append(step_key)


def register_step_keys(job_keys : List[str]) -> None:
	for job_key in job_keys:
		JOB_STORE['step_keys'].append(job_key)
