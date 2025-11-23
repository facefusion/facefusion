from typing import List

from facefusion.types import Args, ArgsStore, Scope


ARGS_STORE : ArgsStore =\
{
	'api': [],
	'cli': [],
	'sys': []
}


def get_api_keys() -> List[str]:
	return ARGS_STORE.get('api')


def get_job_keys() -> List[str]:
	return ARGS_STORE.get('sys')


def get_step_keys() -> List[str]:
	return ARGS_STORE.get('cli')


def register_api_keys(api_keys : List[str]) -> None:
	for api_key in api_keys:
		ARGS_STORE['api'].append(api_key)


def register_args(keys : List[str], scopes : List[Scope]) -> None:
	for key in keys:
		for scope in scopes:
			if scope == 'api':
				ARGS_STORE['api'].append(key)
			if scope == 'cli':
				ARGS_STORE['cli'].append(key)
			if scope == 'sys':
				ARGS_STORE['sys'].append(key)


def get_scope_args(scope : Scope) -> List[str]:
	if scope == 'api':
		return ARGS_STORE.get('api', [])
	if scope == 'cli':
		return ARGS_STORE.get('cli', [])
	if scope == 'sys':
		return ARGS_STORE.get('sys', [])
	return []


def filter_api_args(args : Args) -> Args:
	api_args =\
	{
		key: args[key] for key in args if key in get_api_keys() #type:ignore[literal-required]
	}
	return api_args


def filter_job_args(args : Args) -> Args:
	job_args =\
	{
		key: args[key] for key in args if key in get_job_keys() #type:ignore[literal-required]
	}
	return job_args


def filter_step_args(args : Args) -> Args:
	step_args =\
	{
		key: args[key] for key in args if key in get_step_keys() #type:ignore[literal-required]
	}
	return step_args
