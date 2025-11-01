import importlib
from typing import Optional

from facefusion.types import Language, LocalPoolSet, Locals

LOCAL_POOL_SET : LocalPoolSet = {}
CURRENT_LANGUAGE : Language = 'en'


def __autoload__(module_name : str) -> None:
	try:
		__locals__ = importlib.import_module(module_name + '.locals')
		load(__locals__.LOCALS, module_name)
	except ImportError:
		pass


def load(__locals__ : Locals, module_name : str) -> None:
	LOCAL_POOL_SET[module_name] = __locals__


def get(notation : str, module_name : str = 'facefusion') -> Optional[str]:
	if module_name not in LOCAL_POOL_SET:
		__autoload__(module_name)

	current = LOCAL_POOL_SET.get(module_name).get(CURRENT_LANGUAGE)

	for fragment in notation.split('.'):
		if fragment in current:
			current = current.get(fragment)

			if isinstance(current, str):
				return current

	return None
