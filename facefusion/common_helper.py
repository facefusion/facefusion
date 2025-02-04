<<<<<<< HEAD
from typing import List, Any
import platform


def create_metavar(ranges : List[Any]) -> str:
	return '[' + str(ranges[0]) + '-' + str(ranges[-1]) + ']'


def create_int_range(start : int, end : int, step : int) -> List[int]:
=======
import platform
from typing import Any, Optional, Sequence


def is_linux() -> bool:
	return platform.system().lower() == 'linux'


def is_macos() -> bool:
	return platform.system().lower() == 'darwin'


def is_windows() -> bool:
	return platform.system().lower() == 'windows'


def create_int_metavar(int_range : Sequence[int]) -> str:
	return '[' + str(int_range[0]) + '..' + str(int_range[-1]) + ':' + str(calc_int_step(int_range)) + ']'


def create_float_metavar(float_range : Sequence[float]) -> str:
	return '[' + str(float_range[0]) + '..' + str(float_range[-1]) + ':' + str(calc_float_step(float_range)) + ']'


def create_int_range(start : int, end : int, step : int) -> Sequence[int]:
>>>>>>> origin/master
	int_range = []
	current = start

	while current <= end:
		int_range.append(current)
		current += step
	return int_range


<<<<<<< HEAD
def create_float_range(start : float, end : float, step : float) -> List[float]:
=======
def create_float_range(start : float, end : float, step : float) -> Sequence[float]:
>>>>>>> origin/master
	float_range = []
	current = start

	while current <= end:
		float_range.append(round(current, 2))
		current = round(current + step, 2)
	return float_range


<<<<<<< HEAD
def is_linux() -> bool:
	return to_lower_case(platform.system()) == 'linux'


def is_macos() -> bool:
	return to_lower_case(platform.system()) == 'darwin'


def is_windows() -> bool:
	return to_lower_case(platform.system()) == 'windows'


def to_lower_case(__string__ : Any) -> str:
	return str(__string__).lower()
=======
def calc_int_step(int_range : Sequence[int]) -> int:
	return int_range[1] - int_range[0]


def calc_float_step(float_range : Sequence[float]) -> float:
	return round(float_range[1] - float_range[0], 2)


def cast_int(value : Any) -> Optional[Any]:
	try:
		return int(value)
	except (ValueError, TypeError):
		return None


def cast_float(value : Any) -> Optional[Any]:
	try:
		return float(value)
	except (ValueError, TypeError):
		return None
>>>>>>> origin/master


def get_first(__list__ : Any) -> Any:
	return next(iter(__list__), None)
<<<<<<< HEAD
=======


def get_last(__list__ : Any) -> Any:
	return next(reversed(__list__), None)
>>>>>>> origin/master
