from configparser import ConfigParser
from typing import List, Optional

from facefusion import state_manager
from facefusion.common_helper import cast_bool, cast_float, cast_int

CONFIG_PARSER = None


def get_config_parser() -> ConfigParser:
	global CONFIG_PARSER

	if CONFIG_PARSER is None:
		CONFIG_PARSER = ConfigParser()
		CONFIG_PARSER.read(state_manager.get_item('config_path'), encoding = 'utf-8')
	return CONFIG_PARSER


def clear_config_parser() -> None:
	global CONFIG_PARSER

	CONFIG_PARSER = None


def get_str_value(section : str, option : str, fallback : Optional[str] = None) -> Optional[str]:
	config_parser = get_config_parser()

	if config_parser.has_option(section, option) and config_parser.get(section, option).strip():
		return config_parser.get(section, option)
	return fallback


def get_int_value(section : str, option : str, fallback : Optional[str] = None) -> Optional[int]:
	config_parser = get_config_parser()

	if config_parser.has_option(section, option) and config_parser.get(section, option).strip():
		return config_parser.getint(section, option)
	return cast_int(fallback)


def get_float_value(section : str, option : str, fallback : Optional[str] = None) -> Optional[float]:
	config_parser = get_config_parser()

	if config_parser.has_option(section, option) and config_parser.get(section, option).strip():
		return config_parser.getfloat(section, option)
	return cast_float(fallback)


def get_bool_value(section : str, option : str, fallback : Optional[str] = None) -> Optional[bool]:
	config_parser = get_config_parser()

	if config_parser.has_option(section, option) and config_parser.get(section, option).strip():
		return config_parser.getboolean(section, option)
	return cast_bool(fallback)


def get_str_list(section : str, option : str, fallback : Optional[str] = None) -> Optional[List[str]]:
	config_parser = get_config_parser()

	if config_parser.has_option(section, option) and config_parser.get(section, option).strip():
		return config_parser.get(section, option).split()
	if fallback:
		return fallback.split()
	return None


def get_int_list(section : str, option : str, fallback : Optional[str] = None) -> Optional[List[int]]:
	config_parser = get_config_parser()

	if config_parser.has_option(section, option) and config_parser.get(section, option).strip():
		return list(map(int, config_parser.get(section, option).split()))
	if fallback:
		return list(map(int, fallback.split()))
	return None
