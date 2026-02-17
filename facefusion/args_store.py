from argparse import Action
from typing import List

from facefusion.types import Args, ArgsStore, ArgumentSet, Scope


ARGS_STORE : ArgsStore =\
{
	'api': {},
	'cli': {},
	'sys': {}
}


def get_api_set() -> ArgumentSet:
	return ARGS_STORE.get('api')


def get_cli_set() -> ArgumentSet:
	return ARGS_STORE.get('cli')


def get_sys_set() -> ArgumentSet:
	return ARGS_STORE.get('sys')


def get_api_args() -> List[str]:
	return list(get_api_set().keys())


def get_cli_args() -> List[str]:
	return list(get_cli_set().keys())


def get_sys_args() -> List[str]:
	return list(get_cli_set().keys())


def register_argument(action : Action, scopes : List[Scope]) -> None:
	key = action.dest
	value =\
	{
		'default': action.default
	}

	if action.choices:
		value['choices'] = list(action.choices)

	for scope in scopes:
		if scope == 'api':
			ARGS_STORE['api'][key] = value
		if scope == 'cli':
			ARGS_STORE['cli'][key] = value
		if scope == 'sys':
			ARGS_STORE['sys'][key] = value


def filter_api_args(args : Args) -> Args:
	api_args =\
	{
		key: args.get(key) for key in args if key in ARGS_STORE.get('api') #type:ignore[literal-required]
	}
	return api_args


def filter_sys_args(args : Args) -> Args:
	sys_args =\
	{
		key: args.get(key) for key in args if key in ARGS_STORE.get('sys') #type:ignore[literal-required]
	}
	return sys_args


def filter_cli_args(args : Args) -> Args:
	cli_args =\
	{
		key: args.get(key) for key in args if key in ARGS_STORE.get('cli') #type:ignore[literal-required]
	}
	return cli_args


def filter_step_args(args : Args) -> Args:
	step_args =\
	{
		key: args.get(key) for key in args if key in ARGS_STORE.get('cli') and key not in ARGS_STORE.get('sys') #type:ignore[literal-required]
	}
	return step_args
