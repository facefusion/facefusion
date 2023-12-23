from typing import List, Any
import numpy


def create_metavar(ranges : List[Any]) -> str:
	return '[' + str(ranges[0]) + '-' + str(ranges[-1]) + ']'


def create_range(start : float, stop : float, step : float) -> List[float]:
	return (numpy.around(numpy.arange(start, stop + step, step), decimals = 2)).tolist()
