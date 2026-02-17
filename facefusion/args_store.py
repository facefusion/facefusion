from argparse import Action
from typing import List

from facefusion.types import Args, ArgsStore, Scope


ARGS_STORE : ArgsStore =\
{
	'api': {},
	'cli': {},
	'sys': {}
}


def get_api_set() -> Args:
	return ARGS_STORE.get('api')


def get_cli_set() -> Args:
	return ARGS_STORE.get('cli')


def get_sys_set() -> Args:
	return ARGS_STORE.get('sys')


def get_api_args() -> List[str]:
	return list(get_api_set().keys())


def get_cli_args() -> List[str]:
	return list(get_cli_set().keys())


def get_sys_args() -> List[str]:
	return list(get_sys_set().keys())


def register_arguments(actions : List[Action], scopes : List[Scope]) -> None:
	for action in actions:
		value =\
		{
			'default': action.default
		}

		if action.choices:
			value['choices'] = list(action.choices)

		for scope in scopes:
			if scope == 'api':
				ARGS_STORE['api'][action.dest] = value
			if scope == 'cli':
				ARGS_STORE['cli'][action.dest] = value
			if scope == 'sys':
				ARGS_STORE['sys'][action.dest] = value


def filter_api_args(args : Args) -> Args:
	api_args =\
	{
		key: args.get(key) for key in args if key in get_api_set() #type:ignore[literal-required]
	}
	return api_args


def filter_cli_args(args : Args) -> Args:
	cli_args =\
	{
		key: args.get(key) for key in args if key in get_cli_args() #type:ignore[literal-required]
	}
	return cli_args


def filter_step_args(args : Args) -> Args:
	step_args =\
	{
		key: args.get(key) for key in args if key in get_cli_args() and key not in get_sys_set() #type:ignore[literal-required]
	}
	return step_args


def filter_sys_args(args : Args) -> Args:
	sys_args =\
	{
		key: args.get(key) for key in args if key in get_sys_set() #type:ignore[literal-required]
	}
	return sys_args
