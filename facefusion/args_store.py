from typing import List, Union

from facefusion.processors.types import ProcessorState
from facefusion.types import Args, ArgsStore, State

ARGS_STORE : ArgsStore =\
{
	'api_keys': [],
	'job_keys': [],
	'step_keys': []
}


def get_api_keys() -> List[str]:
	return ARGS_STORE.get('api_keys')


def get_job_keys() -> List[str]:
	return ARGS_STORE.get('job_keys')


def get_step_keys() -> List[str]:
	return ARGS_STORE.get('step_keys')


def register_api_keys(api_keys : List[str]) -> None:
	for api_key in api_keys:
		ARGS_STORE['api_keys'].append(api_key)


def register_job_keys(job_keys : List[str]) -> None:
	for job_key in job_keys:
		ARGS_STORE['job_keys'].append(job_key)


def register_step_keys(step_keys : List[str]) -> None:
	for step_key in step_keys:
		ARGS_STORE['step_keys'].append(step_key)


def filter_api_args(args : Union[Args, State, ProcessorState]) -> Args:
	api_args =\
	{
		key: args[key] for key in args if key in get_api_keys() #type:ignore[literal-required]
	}
	return api_args


def filter_job_args(args : Union[Args, State, ProcessorState]) -> Args:
	job_args =\
	{
		key: args[key] for key in args if key in get_job_keys() #type:ignore[literal-required]
	}
	return job_args


def filter_step_args(args : Union[Args, State, ProcessorState]) -> Args:
	step_args =\
	{
		key: args[key] for key in args if key in get_step_keys() #type:ignore[literal-required]
	}
	return step_args
