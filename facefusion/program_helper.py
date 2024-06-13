from argparse import ArgumentParser, Action
from copy import copy
from typing import List

import facefusion.globals
from facefusion.typing import Args


def validate_args(program : ArgumentParser) -> bool:
	for action in program._actions:
		if action.default and action.choices:
			if isinstance(action.default, list):
				if any(default not in action.choices for default in action.default):
					return False
			elif action.default not in action.choices:
				return False
	return True


def reduce_args(program : ArgumentParser, keys : List[str]) -> ArgumentParser:
	program = copy(program)
	actions : List[Action] = []

	for action in program._actions:
		if action.dest in keys:
			actions.append(action)
	program._actions = actions
	return program


def update_args(program : ArgumentParser, args : Args) -> ArgumentParser:
	program = copy(program)

	for action in program._actions:
		if action.dest in args:
			action.default = args[action.dest]
	return program


def import_globals(program : ArgumentParser, keys : List[str]) -> ArgumentParser:
	program = copy(program)

	for key in keys:
		if hasattr(facefusion.globals, key):
			program = update_args(program,
			{
				key: getattr(facefusion.globals, key)
			})
	return program
