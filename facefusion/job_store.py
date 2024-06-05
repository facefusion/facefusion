from typing import List

from facefusion.typing import JobArgsStore

ARGS_STORE : JobArgsStore =\
{
	'job': [],
	'step': []
}


def get_job_args() -> List[str]:
	return ARGS_STORE.get('job')


def get_step_args() -> List[str]:
	return ARGS_STORE.get('step')


def register_job_args(step_args : List[str]) -> None:
	for step_arg in step_args:
		ARGS_STORE['step'].append(step_arg)


def register_step_args(job_args : List[str]) -> None:
	for job_arg in job_args:
		ARGS_STORE['job'].append(job_arg)
