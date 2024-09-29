from argparse import ArgumentParser

import pytest

from facefusion.program_helper import find_argument_group, remove_args, validate_actions


def test_find_argument_group() -> None:
	program = ArgumentParser()
	program.add_argument_group('test-1')
	program.add_argument_group('test-2')

	assert find_argument_group(program, 'test-1')
	assert find_argument_group(program, 'test-2')
	assert find_argument_group(program, 'invalid') is None


@pytest.mark.skip()
def test_validate_args() -> None:
	pass


def test_validate_actions() -> None:
	program = ArgumentParser()
	program.add_argument('--test-1', default = 'test_1', choices = [ 'test_1', 'test_2' ])
	program.add_argument('--test-2', default = 'test_2', choices= [ 'test_1', 'test_2' ], nargs = '+')

	assert validate_actions(program) is True

	args =\
	{
		'test_1': 'test_2',
		'test_2': [ 'test_1', 'test_3' ]
	}

	for action in program._actions:
		if action.dest in args:
			action.default = args[action.dest]

	assert validate_actions(program) is False


def test_remove_args() -> None:
	program = ArgumentParser()
	program.add_argument('--test-1')
	program.add_argument('--test-2')
	program.add_argument('--test-3')

	actions = [ action.dest for action in program._actions ]

	assert 'test_1' in actions
	assert 'test_2' in actions
	assert 'test_3' in actions

	program = remove_args(program, [ 'test_1', 'test_2' ])
	actions = [ action.dest for action in program._actions ]

	assert 'test_1' not in actions
	assert 'test_2' not in actions
	assert 'test_3' in actions
