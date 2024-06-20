from argparse import ArgumentParser

from facefusion.program_helper import find_argument_group, validate_args, reduce_args, update_args


def test_find_argument_group() -> None:
	program = ArgumentParser()
	program.add_argument_group('test-1')
	program.add_argument_group('test-2')

	assert find_argument_group(program, 'test-1')
	assert find_argument_group(program, 'test-2')
	assert find_argument_group(program, 'invalid') is None


def test_validate_args() -> None:
	program = ArgumentParser()
	program.add_argument('--test-1', default = 'test_1', choices = [ 'test_1', 'test_2' ])
	program.add_argument('--test-2', default = 'test_2', choices= [ 'test_1', 'test_2' ], nargs = '+')

	assert validate_args(program) is True

	update_args(program,
	{
		'test_1': 'test_3'
	})

	assert validate_args(program) is False

	update_args(program,
	{
		'test_1': 'test_2',
		'test_2': [ 'test_1', 'test_3' ]
	})

	assert validate_args(program) is False


def test_reduce_args() -> None:
	program = ArgumentParser()
	program.add_argument('-t1', '--test-1', dest = 'test_1', default = 'test_1')
	program.add_argument('-t2', '--test-2', dest = 'test_2', default = 'test_2')
	program.add_argument('-t3', '--test-3', dest = 'test_3', default = 'test_3')
	program.add_argument('-t4', '--test-4', dest = 'test_4', default = 'test_4')
	program.add_argument('--test-5', default = 'test_5')
	program.add_argument('--test-6', default = 'test_6')

	program = reduce_args(program, [ 'test_1', 'test_3', 'test_5' ])
	known_args, _ = program.parse_known_args()

	assert known_args.test_1 == 'test_1'
	assert known_args.test_3 == 'test_3'
	assert known_args.test_5 == 'test_5'
	assert 'test_2' not in known_args
	assert 'test_4' not in known_args
	assert 'test_6' not in known_args


def test_update_args() -> None:
	program = ArgumentParser()
	program.add_argument('-t1', '--test-1', dest = 'test_1', default = 'test_1')
	program.add_argument('-t2', '--test-2', dest = 'test_2', default = 'test_2')
	program.add_argument('--test-3', default = 'test_3')
	program.add_argument('--test-4', default = 'test_4')

	program = update_args(program,
	{
		'test_1': 'update_1',
		'test_3': 'update_3'
	})
	known_args, _ = program.parse_known_args()

	assert known_args.test_1 == 'update_1'
	assert known_args.test_3 == 'update_3'
	assert known_args.test_2 == 'test_2'
	assert known_args.test_4 == 'test_4'
