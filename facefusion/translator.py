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


def set_language(language : Language) -> None:
	global CURRENT_LANGUAGE
	CURRENT_LANGUAGE = language


def get_language() -> Language:
	return CURRENT_LANGUAGE


def get(notation : str, module_name : str = 'facefusion') -> Optional[str]:
	if module_name not in LOCALE_POOL_SET:
		__autoload__(module_name)

	module_locales = LOCALE_POOL_SET.get(module_name)
	if not module_locales:
		return None

	current = module_locales.get(CURRENT_LANGUAGE)
	if not current:
		# Fallback to English if current language not available
		current = module_locales.get('en')
	if not current:
		return None

	for fragment in notation.split('.'):
		if isinstance(current, dict) and fragment in current:
			current = current.get(fragment)

			if isinstance(current, str):
				return current
		else:
			return None

	return None
