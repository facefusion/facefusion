import platform
from typing import Any, List


def is_linux() -> bool:
	return platform.system().lower() == 'linux'


def is_macos() -> bool:
	return platform.system().lower() == 'darwin'


def is_windows() -> bool:
	return platform.system().lower() == 'windows'


def create_metavar(ranges : List[Any]) -> str:
	return '[' + str(ranges[0]) + '..' + str(ranges[-1]) + ':' + str(ranges[1] - ranges[0]) + ']'


def create_int_range(start : int, end : int, step : int) -> List[int]:
	int_range = []
	current = start

	while current <= end:
		int_range.append(current)
		current += step
	return int_range


def create_float_range(start : float, end : float, step : float) -> List[float]:
	float_range = []
	current = start

	while current <= end:
		float_range.append(round(current, 2))
		current = round(current + step, 2)
	return float_range


def map_float(value : float, start : float, end : float, map_start : float, map_end : float) -> float:
	ratio = (value - start) / (end - start)
	map_value = map_start + (map_end - map_start) * ratio
	return map_value


def get_first(__list__ : Any) -> Any:
	return next(iter(__list__), None)


def get_last(__list__ : Any) -> Any:
	return next(reversed(__list__), None)
