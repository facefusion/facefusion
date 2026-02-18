from argparse import Action
from typing import Dict, List

from facefusion.types import Args, ArgumentSet, ArgumentStore, Scope, State

ARGUMENT_STORE : ArgumentStore =\
{
	'api': {},
	'cli': {},
	'sys': {}
}


def get_api_argument_set() -> Dict[str, ArgumentSet]:
	return ARGUMENT_STORE.get('api')


def get_cli_argument_set() -> Dict[str, ArgumentSet]:
	return ARGUMENT_STORE.get('cli')


def get_sys_argument_set() -> Dict[str, ArgumentSet]:
	return ARGUMENT_STORE.get('sys')


def get_api_arguments() -> List[str]:
	return list(get_api_argument_set().keys())


def get_cli_arguments() -> List[str]:
	return list(get_cli_argument_set().keys())


def get_sys_arguments() -> List[str]:
	return list(get_sys_argument_set().keys())


def register_argument_set(actions : List[Action], scopes : List[Scope]) -> None:
	for action in actions:
		value : ArgumentSet =\
		{
			'default': action.default
		}

		if action.choices:
			value['choices'] = list(action.choices)

		for scope in scopes:
			if scope == 'api':
				ARGUMENT_STORE['api'][action.dest] = value
			if scope == 'cli':
				ARGUMENT_STORE['cli'][action.dest] = value
			if scope == 'sys':
				ARGUMENT_STORE['sys'][action.dest] = value


def filter_api_args(state : State) -> Args:
	api_args =\
	{
		key: state.get(key) for key in state if key in get_api_arguments()
	}
	return api_args


def filter_cli_args(state : State) -> Args:
	cli_args =\
	{
		key: state.get(key) for key in state if key in get_cli_arguments()
	}
	return cli_args


def filter_step_args(args : Args) -> Args:
	step_args =\
	{
		key: args.get(key) for key in args if key in get_cli_arguments() and key not in get_sys_arguments()
	}
	return step_args


def filter_sys_args(state : State) -> Args:
	sys_args =\
	{
		key: state.get(key) for key in state if key in get_sys_arguments()
	}
	return sys_args
