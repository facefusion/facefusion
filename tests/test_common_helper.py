from facefusion.common_helper import calculate_float_step, calculate_int_step, create_float_metavar, create_float_range, create_int_metavar, create_int_range, get_middle


def test_create_int_metavar() -> None:
	assert create_int_metavar([ 1, 2, 3, 4, 5 ]) == '[1..5:1]'


def test_create_float_metavar() -> None:
	assert create_float_metavar([ 0.1, 0.2, 0.3, 0.4, 0.5 ]) == '[0.1..0.5:0.1]'


def test_create_int_range() -> None:
	assert create_int_range(0, 2, 1) == [ 0, 1, 2 ]
	assert create_float_range(0, 1, 1) == [ 0, 1 ]


def test_create_float_range() -> None:
	assert create_float_range(0.0, 1.0, 0.5) == [ 0.0, 0.5, 1.0 ]
	assert create_float_range(0.0, 0.5, 0.05) == [ 0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50 ]


def test_calc_int_step() -> None:
	assert calculate_int_step([ 0, 1 ]) == 1


def test_calc_float_step() -> None:
	assert calculate_float_step([ 0.1, 0.2 ]) == 0.1


def test_get_middle() -> None:
	assert get_middle([ 1, 2, 3, 4, 5 ]) == 3
	assert get_middle([ 1 ]) == 1
