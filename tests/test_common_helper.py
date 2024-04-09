from facefusion.common_helper import create_metavar, create_int_range, create_float_range


def test_create_metavar() -> None:
	assert create_metavar([ 1, 2, 3, 4, 5 ]) == '[1-5]'


def test_create_int_range() -> None:
	assert create_int_range(0, 2, 1) == [ 0, 1, 2 ]
	assert create_float_range(0, 1, 1) == [ 0, 1 ]


def test_create_float_range() -> None:
	assert create_float_range(0.0, 1.0, 0.5) == [ 0.0, 0.5, 1.0 ]
	assert create_float_range(0.0, 0.2, 0.05) == [ 0.0, 0.05, 0.10, 0.15, 0.20 ]

