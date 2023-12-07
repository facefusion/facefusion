from typing import Any, List


def create_metavar(ranges : List[Any]) -> str:
	return '[' + str(ranges[0]) + '-' + str(ranges[-1]) + ']'


def update_status(message : str, scope : str = 'FACEFUSION.CORE') -> None:
	print('[' + scope + '] ' + message)
