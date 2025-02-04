from argparse import ArgumentParser

import pytest

from facefusion.program_helper import find_argument_group, validate_actions


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
