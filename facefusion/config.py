import os
import configparser
from configparser import ConfigParser
from typing import Any, Dict, List, Optional

from facefusion import logger, state_manager
from facefusion.common_helper import cast_bool, cast_float, cast_int

CONFIG_PARSER = None
CONFIG_DEFAULTS : Dict[str, Dict[str, Any]] = {}


def get_config_parser() -> ConfigParser:
	global CONFIG_PARSER

	if CONFIG_PARSER is None:
		CONFIG_PARSER = ConfigParser()
		CONFIG_PARSER.read(state_manager.get_item('config_path'), encoding = 'utf-8')
	return CONFIG_PARSER


def clear_config_parser() -> None:
	global CONFIG_PARSER

	CONFIG_PARSER = None


def register_default(section : str, option : str, fallback : Any) -> None:
	if section not in CONFIG_DEFAULTS:
		CONFIG_DEFAULTS[section] = {}
	if option not in CONFIG_DEFAULTS[section]:
		CONFIG_DEFAULTS[section][option] = fallback


def get_str_value(section : str, option : str, fallback : Optional[str] = None) -> Optional[str]:
	config_parser = get_config_parser()
	register_default(section, option, fallback)

	if config_parser.has_option(section, option) and config_parser.get(section, option).strip():
		return config_parser.get(section, option)
	return fallback


def get_int_value(section : str, option : str, fallback : Optional[str] = None) -> Optional[int]:
	config_parser = get_config_parser()
	value = cast_int(fallback)
	register_default(section, option, value)

	if config_parser.has_option(section, option) and config_parser.get(section, option).strip():
		return config_parser.getint(section, option)
	return value


def get_float_value(section : str, option : str, fallback : Optional[str] = None) -> Optional[float]:
	config_parser = get_config_parser()
	value = cast_float(fallback)
	register_default(section, option, value)

	if config_parser.has_option(section, option) and config_parser.get(section, option).strip():
		return config_parser.getfloat(section, option)
	return value


def get_bool_value(section : str, option : str, fallback : Optional[str] = None) -> Optional[bool]:
	config_parser = get_config_parser()
	value = cast_bool(fallback)
	register_default(section, option, value)

	if config_parser.has_option(section, option) and config_parser.get(section, option).strip():
		return config_parser.getboolean(section, option)
	return value


def get_str_list(section : str, option : str, fallback : Optional[str] = None) -> Optional[List[str]]:
	config_parser = get_config_parser()
	value = fallback.split() if fallback else None
	register_default(section, option, value)

	if config_parser.has_option(section, option) and config_parser.get(section, option).strip():
		return config_parser.get(section, option).split()
	if fallback:
		return fallback.split()
	return value


def get_int_list(section : str, option : str, fallback : Optional[str] = None) -> Optional[List[int]]:
	config_parser = get_config_parser()
	value = list(map(int, fallback.split())) if fallback else None
	register_default(section, option, value)

	if config_parser.has_option(section, option) and config_parser.get(section, option).strip():
		value_from_config = config_parser.get(section, option)
		cleaned_value = value_from_config.strip().strip('()').replace(',', ' ')
		return list(map(int, cleaned_value.split()))
	return value


def save_defaults() -> None:
	config_path = state_manager.get_item('config_path')
	config = configparser.ConfigParser()
	if os.path.isfile(config_path):
		config.read(config_path, encoding = 'utf-8')

	for section, options in CONFIG_DEFAULTS.items():
		if not config.has_section(section):
			config.add_section(section)
		for key, default_value in options.items():
			try:
				current_value = state_manager.get_item(key)

				if current_value == default_value:
					value_str = ''
				else:
					value_str = ''
					if current_value is not None:
						if isinstance(current_value, bool):
							value_str = str(current_value).lower()
						elif isinstance(current_value, (list, tuple)):
							value_str = ' '.join(map(str, current_value))
						else:
							value_str = str(current_value)
				config.set(section, key, value_str)
			except (KeyError, TypeError):
				config.set(section, key, '')

	with open(config_path, 'w', encoding = 'utf-8') as config_file:
		config.write(config_file)
