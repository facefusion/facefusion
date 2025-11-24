from typing import List

from facefusion.types import Args, ArgsStore, Scope


ARGS_STORE : ArgsStore =\
{
	'api': [],
	'cli': [],
	'sys': []
}


def get_api_args() -> List[str]:
	return ARGS_STORE.get('api')


def get_sys_args() -> List[str]:
	return ARGS_STORE.get('sys')


def get_cli_args() -> List[str]:
	return ARGS_STORE.get('cli')


def register_args(keys : List[str], scopes : List[Scope]) -> None:
	for key in keys:
		for scope in scopes:
			if scope == 'api':
				ARGS_STORE['api'].append(key)
			if scope == 'cli':
				ARGS_STORE['cli'].append(key)
			if scope == 'sys':
				ARGS_STORE['sys'].append(key)


def filter_api_args(args : Args) -> Args:
	api_args =\
	{
		key: args.get(key) for key in args if key in get_api_args() #type:ignore[literal-required]
	}
	return api_args


def filter_sys_args(args : Args) -> Args:
	sys_args =\
	{
		key: args.get(key) for key in args if key in get_sys_args() #type:ignore[literal-required]
	}
	return sys_args


def filter_cli_args(args : Args) -> Args:
	cli_args =\
	{
		key: args.get(key) for key in args if key in get_cli_args() #type:ignore[literal-required]
	}
	return cli_args


def filter_step_args(args : Args) -> Args:
	step_args =\
	{
		key: args.get(key) for key in args if key in get_cli_args() and key not in get_sys_args() #type:ignore[literal-required]
	}
	return step_args
