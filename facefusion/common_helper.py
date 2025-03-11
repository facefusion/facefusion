import platform
from typing import Any, Iterable, Optional, Reversible, Sequence


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
	int_range = []
	current = start

	while current <= end:
		int_range.append(current)
		current += step
	return int_range


def create_float_range(start : float, end : float, step : float) -> Sequence[float]:
	float_range = []
	current = start

	while current <= end:
		float_range.append(round(current, 2))
		current = round(current + step, 2)
	return float_range


def calc_int_step(int_range : Sequence[int]) -> int:
	return int_range[1] - int_range[0]


def calc_float_step(float_range : Sequence[float]) -> float:
	return round(float_range[1] - float_range[0], 2)


def cast_int(value : Any) -> Optional[int]:
	try:
		return int(value)
	except (ValueError, TypeError):
		return None


def cast_float(value : Any) -> Optional[float]:
	try:
		return float(value)
	except (ValueError, TypeError):
		return None


def cast_bool(value : Any) -> Optional[bool]:
	if value == 'True':
		return True
	if value == 'False':
		return False
	return None


def get_first(__list__ : Any) -> Any:
	if isinstance(__list__, Iterable):
		return next(iter(__list__), None)
	return None


def get_last(__list__ : Any) -> Any:
	if isinstance(__list__, Reversible):
		return next(reversed(__list__), None)
	return None
