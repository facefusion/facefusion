from argparse import Action
from typing import List

from facefusion.types import ArgumentSet, ArgumentStore, Scope, State

ARGUMENT_STORE : ArgumentStore =\
{
	'api': {},
	'cli': {},
	'sys': {}
}


def get_api_argument_set() -> ArgumentSet:
	return ARGUMENT_STORE.get('api')


def get_cli_argument_set() -> ArgumentSet:
	return ARGUMENT_STORE.get('cli')


def get_sys_argument_set() -> ArgumentSet:
	return ARGUMENT_STORE.get('sys')


def get_api_arguments() -> List[str]:
	return list(get_api_argument_set().keys())


def get_cli_arguments() -> List[str]:
	return list(get_cli_argument_set().keys())


def get_sys_arguments() -> List[str]:
	return list(get_sys_argument_set().keys())


def register_argument_set(actions : List[Action], scopes : List[Scope]) -> None:
	for action in actions:
		value =\
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


def filter_api_argument_set(state : State) -> ArgumentSet:
	api_argument_set =\
	{
		key: state.get(key) for key in state if key in get_api_argument_set()
	}
	return api_argument_set


def filter_cli_argument_set(state : State) -> ArgumentSet:
	cli_argument_set =\
	{
		key: state.get(key) for key in state if key in get_cli_arguments()
	}
	return cli_argument_set


def filter_step_argument_set(state : State) -> ArgumentSet:
	step_argument_set =\
	{
		key: state.get(key) for key in state if key in get_cli_arguments() and key not in get_sys_argument_set()
	}
	return step_argument_set


def filter_sys_argument_set(state : State) -> ArgumentSet:
	sys_argument_set =\
	{
		key: state.get(key) for key in state if key in get_sys_argument_set()
	}
	return sys_argument_set
