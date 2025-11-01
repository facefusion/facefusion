from typing import Sequence


def sanitize_int_range(value : int, int_range : Sequence[int]) -> int:
	if value in int_range:
		return value
	return int_range[0]
