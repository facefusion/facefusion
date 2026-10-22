from argparse import Action
from typing import List

from facefusion.types import Capability, CapabilityCategory, CapabilitySet, CapabilityStore, Category, Scope

CAPABILITY_STORE : CapabilityStore =\
{
	'api': {},
	'cli': {},
	'sys': {}
}


def get_api_capability_category() -> CapabilityCategory:
	capability_category : CapabilityCategory = {}

	for name, value in CAPABILITY_STORE.get('api').items():
		for category in value.get('categories'):
			capability_category.setdefault(category, {})[name] = value

	return capability_category


def get_api_capability_set() -> CapabilitySet:
	return CAPABILITY_STORE.get('api')


def get_cli_capability_set() -> CapabilitySet:
	return CAPABILITY_STORE.get('cli')


def get_sys_capability_set() -> CapabilitySet:
	return CAPABILITY_STORE.get('sys')


def get_api_arguments() -> List[str]:
	return list(get_api_capability_set().keys())


def get_cli_arguments() -> List[str]:
	return list(get_cli_capability_set().keys())


def get_sys_arguments() -> List[str]:
	return list(get_sys_capability_set().keys())


def register_capability_set(actions : List[Action], scopes : List[Scope], categories : List[Category]) -> None:
	for action in actions:
		value : Capability =\
		{
			'default': action.default,
			'categories': categories
		}

		if action.choices:
			value['choices'] = list(action.choices)

		for scope in scopes:
			if scope == 'api':
				CAPABILITY_STORE['api'][action.dest] = value
			if scope == 'cli':
				CAPABILITY_STORE['cli'][action.dest] = value
			if scope == 'sys':
				CAPABILITY_STORE['sys'][action.dest] = value
