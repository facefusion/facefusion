from configparser import ConfigParser
from typing import Any, Optional, List

from facefusion.filesystem import resolve_relative_path

CONFIG = None


def get_config() -> ConfigParser:
	global CONFIG

	if CONFIG is None:
		config_path = resolve_relative_path('../facefusion.ini')
		CONFIG = ConfigParser()
		CONFIG.read(config_path)
	return CONFIG


def clear_config() -> None:
	global CONFIG

	CONFIG = None


def get_str_value(key : str, fallback : Optional[str] = None) -> Optional[str]:
	value = find_value_by_section(key)

	if value or fallback:
		return str(value or fallback)
	return None


def get_int_value(key : str, fallback : Optional[str] = None) -> Optional[int]:
	value = find_value_by_section(key)

	if value or fallback:
		return int(value or fallback)
	return None


def get_float_value(key : str, fallback : Optional[str] = None) -> Optional[float]:
	value = find_value_by_section(key)

	if value or fallback:
		return float(value or fallback)
	return None


def get_bool_value(key : str, fallback : Optional[str] = None) -> Optional[bool]:
	value = find_value_by_section(key)

	if value == 'True' or fallback == 'True':
		return True
	if value == 'False' or fallback == 'False':
		return False
	return None


def get_str_list(key : str, fallback : Optional[str] = None) -> Optional[List[str]]:
	value = find_value_by_section(key)

	if value or fallback:
		return [ str(value) for value in (value or fallback).split(' ') ]
	return None


def get_int_list(key : str, fallback : Optional[str] = None) -> Optional[List[int]]:
	value = find_value_by_section(key)

	if value or fallback:
		return [ int(value) for value in (value or fallback).split(' ') ]
	return None


def get_float_list(key : str, fallback : Optional[str] = None) -> Optional[List[float]]:
	value = find_value_by_section(key)

	if value or fallback:
		return [ float(value) for value in (value or fallback).split(' ') ]
	return None


def find_value_by_section(key : str) -> Optional[Any]:
	config = get_config()
	section, option = key.split('.')

	if section in config and option in config[section]:
		return config[section][option]
	return None
