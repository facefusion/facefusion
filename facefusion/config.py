from configparser import ConfigParser
from typing import Optional, List

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
	section, option = key.split('.')
	value = get_config()[section].get(option)
	if value or fallback:
		return str(value or fallback)
	return None


def get_int_value(key : str, fallback : Optional[str] = None) -> Optional[int]:
	section, option = key.split('.')
	value = get_config()[section].get(option)
	if value or fallback:
		return int(value or fallback)
	return None


def get_float_value(key : str, fallback : Optional[str] = None) -> Optional[float]:
	section, option = key.split('.')
	value = get_config()[section].get(option)
	if value or fallback:
		return float(value or fallback)
	return None


def get_bool_value(key : str, fallback : Optional[str] = None) -> Optional[bool]:
	section, option = key.split('.')
	value = get_config()[section].get(option, fallback)
	if value == 'True' or fallback == 'True':
		return True
	if value == 'False' or fallback == 'False':
		return False
	return None


def get_str_list(key : str, fallback : Optional[str] = None) -> Optional[List[str]]:
	section, option = key.split('.')
	value = get_config()[section].get(option)
	if value or fallback:
		return [ str(value) for value in (value or fallback).split(' ') ]
	return None


def get_int_list(key : str, fallback : Optional[str] = None) -> Optional[List[int]]:
	section, option = key.split('.')
	value = get_config()[section].get(option)
	if value or fallback:
		return [ int(value) for value in (value or fallback).split(' ') ]
	return None


def get_float_list(key : str, fallback : Optional[str] = None) -> Optional[List[float]]:
	section, option = key.split('.')
	value = get_config()[section].get(option)
	if value or fallback:
		return [ float(value) for value in (value or fallback).split(' ') ]
	return None
