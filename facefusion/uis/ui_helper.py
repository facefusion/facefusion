from typing import Optional


def convert_int_none(value : int) -> Optional[int]:
	if value != 'none':
		return value
	return None


def convert_str_none(value : str) -> Optional[str]:
	if value != 'none':
		return value
	return None
