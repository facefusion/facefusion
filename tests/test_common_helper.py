from unittest.mock import patch

from facefusion.common_helper import calculate_float_step, calculate_int_step, cast_bool, cast_float, cast_int, create_float_metavar, create_float_range, create_int_metavar, create_int_range, get_first, get_last, get_middle, is_linux, is_macos, is_windows


def test_is_linux() -> None:
	with patch('platform.system', return_value = 'Linux'):
		assert is_linux() is True
	with patch('platform.system', return_value = 'Darwin'):
		assert is_linux() is False


def test_is_macos() -> None:
	with patch('platform.system', return_value = 'Darwin'):
		assert is_macos() is True
	with patch('platform.system', return_value = 'Windows'):
		assert is_macos() is False


def test_is_windows() -> None:
	with patch('platform.system', return_value = 'Windows'):
		assert is_windows() is True
	with patch('platform.system', return_value = 'Linux'):
		assert is_windows() is False


def test_create_int_metavar() -> None:
	assert create_int_metavar([ 1, 2, 3, 4, 5 ]) == '[1..5:1]'
	assert create_int_metavar([ 0, 25, 50, 75, 100 ]) == '[0..100:25]'


def test_create_float_metavar() -> None:
	assert create_float_metavar([ 0.1, 0.2, 0.3, 0.4, 0.5 ]) == '[0.1..0.5:0.1]'
	assert create_float_metavar([ 0.0, 0.25, 0.5 ]) == '[0.0..0.5:0.25]'


def test_create_int_range() -> None:
	assert create_int_range(0, 2, 1) == [ 0, 1, 2 ]
	assert create_int_range(0, 100, 25) == [ 0, 25, 50, 75, 100 ]
	assert create_int_range(1, 10, 4) == [ 1, 5, 9 ]
	assert create_int_range(5, 5, 1) == [ 5 ]
	assert create_int_range(6, 5, 1) == []


def test_create_float_range() -> None:
	assert create_float_range(0, 1, 1) == [ 0, 1 ]
	assert create_float_range(0.0, 1.0, 0.5) == [ 0.0, 0.5, 1.0 ]
	assert create_float_range(0.0, 0.5, 0.05) == [ 0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50 ]
	assert create_float_range(0.0, 1.0, 0.1) == [ 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0 ]
	assert len(create_float_range(0.0, 1.0, 0.01)) == 101
	assert create_float_range(0.0, 1.0, 0.01)[-1] == 1.0


def test_calculate_int_step() -> None:
	assert calculate_int_step([ 0, 1 ]) == 1
	assert calculate_int_step([ 0, 25, 50 ]) == 25


def test_calculate_float_step() -> None:
	assert calculate_float_step([ 0.1, 0.2 ]) == 0.1
	assert calculate_float_step([ 0.0, 0.05, 0.1 ]) == 0.05


def test_cast_int() -> None:
	assert cast_int(1) == 1
	assert cast_int('1') == 1
	assert cast_int(1.9) == 1
	assert cast_int('invalid') is None
	assert cast_int(None) is None


def test_cast_float() -> None:
	assert cast_float(1) == 1.0
	assert cast_float('0.5') == 0.5
	assert cast_float('invalid') is None
	assert cast_float(None) is None


def test_cast_bool() -> None:
	assert cast_bool('True') is True
	assert cast_bool('False') is False
	assert cast_bool('true') is None
	assert cast_bool('invalid') is None


def test_get_first() -> None:
	assert get_first([ 1, 2, 3 ]) == 1
	assert get_first(( 1, 2, 3 )) == 1
	assert get_first([]) is None
	assert get_first(None) is None


def test_get_middle() -> None:
	assert get_middle([ 1, 2, 3, 4, 5 ]) == 3
	assert get_middle([ 1, 2, 3, 4 ]) == 3
	assert get_middle([ 1 ]) == 1
	assert get_middle([]) is None
	assert get_middle(None) is None


def test_get_last() -> None:
	assert get_last([ 1, 2, 3 ]) == 3
	assert get_last(( 1, 2, 3 )) == 3
	assert get_last([]) is None
	assert get_last(None) is None
