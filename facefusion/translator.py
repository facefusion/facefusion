from typing import Optional

from facefusion.types import LocalPoolSet, Locals

LOCAL_POOL_SET : LocalPoolSet = {}


def load(__locals__ : Locals, module_name : str) -> None:
	LOCAL_POOL_SET[module_name] = __locals__


def get(notation : str, module_name : str) -> Optional[str]:
	current = LOCAL_POOL_SET[module_name].get('en')

	for fragment in notation.split('.'):
		if fragment in current:
			current = current.get(fragment)

			if isinstance(current, str):
				return current

	return None
