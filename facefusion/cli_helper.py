from typing import List, Any


def create_metavar(ranges : List[Any]) -> str:
	return '[' + str(ranges[0]) + '-' + str(ranges[-1]) + ']'
