from typing import List, Any, Tuple
import numpy


def create_metavar(ranges : List[Any]) -> str:
	return '[' + str(ranges[0]) + '-' + str(ranges[-1]) + ']'


def create_int_range(start : int, stop : int, step : int) -> List[int]:
	return (numpy.arange(start, stop + step, step)).tolist()


def create_float_range(start : float, stop : float, step : float) -> List[float]:
	return (numpy.around(numpy.arange(start, stop + step, step), decimals = 2)).tolist()


def get_first(__list__ : Any) -> Any:
	return next(iter(__list__), None)


def extract_major_version(version : str) -> Tuple[int, int]:
	versions = version.split('.')
	if len(versions) > 1:
		return int(versions[0]), int(versions[1])
	if len(versions) == 1:
		return int(versions[0]), 0
	return 0, 0
