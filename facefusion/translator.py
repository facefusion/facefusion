import importlib
from typing import Optional

from facefusion.types import Language, LocalePoolSet, Locales

LOCALE_POOL_SET : LocalePoolSet = {}
CURRENT_LANGUAGE : Language = 'en'


def __autoload__(module_name : str) -> None:
	try:
		__locales__ = importlib.import_module(module_name + '.locales')
		load(__locales__.LOCALES, module_name)
	except ImportError:
		pass


def load(__locales__ : Locales, module_name : str) -> None:
	LOCALE_POOL_SET[module_name] = __locales__


def get(notation : str, module_name : str = 'facefusion') -> Optional[str]:
	if module_name not in LOCALE_POOL_SET:
		__autoload__(module_name)

	current = LOCALE_POOL_SET.get(module_name).get(CURRENT_LANGUAGE)

	for fragment in notation.split('.'):
		if fragment in current:
			current = current.get(fragment)

			if isinstance(current, str):
				return current

	return None
