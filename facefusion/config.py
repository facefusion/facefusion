from configparser import ConfigParser
from typing import Any, Optional, List
import os.path 
from facefusion.filesystem import resolve_relative_path
import facefusion.globals

CONFIG = None


def get_config(config_file_path: str = None) -> ConfigParser:
    global CONFIG
	
    if CONFIG is None:  # Only read from file if CONFIG is not initialized
        if config_file_path is not None:
            resolved_path = config_file_path
        else:
            config_file_path = facefusion.globals.ini_path  
            if config_file_path is not None:
                if os.path.isabs(config_file_path):  
                    resolved_path = config_file_path
                else:
                    resolved_path = resolve_relative_path(config_file_path)
            else:
                resolved_path = resolve_relative_path('../facefusion.ini')# Default path
        CONFIG = ConfigParser()
        CONFIG.read(resolved_path, encoding='utf-8')
    return CONFIG  # Always return the CONFIG object

def clear_config() -> None:
	global CONFIG
	
	CONFIG = None


def get_str_value(key : str, fallback : Optional[str] = None) -> Optional[str]:
	value = get_value_by_notation(key)

	if value or fallback:
		return str(value or fallback)
	return None


def get_int_value(key : str, fallback : Optional[str] = None) -> Optional[int]:
	value = get_value_by_notation(key)

	if value or fallback:
		return int(value or fallback)
	return None


def get_float_value(key : str, fallback : Optional[str] = None) -> Optional[float]:
	value = get_value_by_notation(key)

	if value or fallback:
		return float(value or fallback)
	return None


def get_bool_value(key : str, fallback : Optional[str] = None) -> Optional[bool]:
	value = get_value_by_notation(key)

	if value == 'True' or fallback == 'True':
		return True
	if value == 'False' or fallback == 'False':
		return False
	return None


def get_str_list(key : str, fallback : Optional[str] = None) -> Optional[List[str]]:
	value = get_value_by_notation(key)

	if value or fallback:
		return [ str(value) for value in (value or fallback).split(' ') ]
	return None


def get_int_list(key : str, fallback : Optional[str] = None) -> Optional[List[int]]:
	value = get_value_by_notation(key)

	if value or fallback:
		return [ int(value) for value in (value or fallback).split(' ') ]
	return None


def get_float_list(key : str, fallback : Optional[str] = None) -> Optional[List[float]]:
	value = get_value_by_notation(key)

	if value or fallback:
		return [ float(value) for value in (value or fallback).split(' ') ]
	return None


def get_value_by_notation(key : str) -> Optional[Any]:
	config = get_config()

	if '.' in key:
		section, name = key.split('.')
		if section in config and name in config[section]:
			return config[section][name]
	if key in config:
		return config[key]
	return None
