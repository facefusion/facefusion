from argparse import ArgumentParser, Action
from copy import copy
from typing import List

from facefusion.typing import Args


def validate_args(program : ArgumentParser) -> None:
	try:
		for action in program._actions:
			if action.default:
				if isinstance(action.default, list):
					for default in action.default:
						program._check_value(action, default)
				else:
					program._check_value(action, action.default)
	except Exception as exception:
		program.error(str(exception))


def reduce_args(program : ArgumentParser, keys : List[str]) -> ArgumentParser:
	program = copy(program)
	actions : List[Action] = []

	for action in program._actions:
		if any(option_string in keys for option_string in action.option_strings):
			actions.append(action)
	program._actions = actions
	return program


def update_args(program : ArgumentParser, args : Args) -> ArgumentParser:
	program = copy(program)

	for action in program._actions:
		if action.dest in args:
			action.default = args[action.dest]
	return program
