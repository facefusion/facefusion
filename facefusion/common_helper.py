from typing import List, Any
import numpy


def create_metavar(ranges : List[Any]) -> str:
	return '[' + str(ranges[0]) + '-' + str(ranges[-1]) + ']'


def create_int_range(start : int, stop : int, step : int) -> List[int]:
	return (numpy.arange(start, stop + step, step)).tolist()


def create_float_range(start : float, stop : float, step : float) -> List[float]:
	return (numpy.around(numpy.arange(start, stop + step, step), decimals = 2)).tolist()


def get_first(__list__ : Any) -> Any:
	return next(iter(__list__), None)
