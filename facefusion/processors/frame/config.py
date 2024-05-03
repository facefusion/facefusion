from typing import List, Optional, Any
from configparser import ConfigParser
from types import ModuleType
from facefusion.config import get_config
from facefusion.execution import encode_execution_providers
import facefusion.globals
import facefusion.choices
import facefusion.processors.frame.globals as frameglobals
import facefusion.processors.frame.choices as framechoices

CONFIG_PATH: Optional[str] = None


def init_config(config_path: str) -> None:
    global CONFIG_PATH
    CONFIG_PATH = config_path


def read_config() -> ConfigParser:
    config = get_config()
    with open(CONFIG_PATH, 'r') as configfile:
        config.read_file(configfile)
    return config


def write_config(config: ConfigParser) -> None:
    with open(CONFIG_PATH, 'w') as configfile:
        config.write(configfile)


def parse_config() -> ConfigParser:
    modules = [facefusion.globals, facefusion.choices, frameglobals, framechoices]
    config = get_values(modules)
    return config


def get_values(modules: List[ModuleType]) -> ConfigParser:
    config = get_config()
    for section in config.sections():
        for key in config[section].keys():
            for module in modules:
                attr_value = getattr(module, key, None)
                if attr_value is not None:
                    if key == 'execution_providers':
                        attr_value = ' '.join(encode_execution_providers(attr_value))
                    config[section][key] = format_value(attr_value)
                    break
            else:
                config[section][key] = ''
    return config


def format_value(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return ' '.join(map(str, value))
    return str(value)


def save_config() -> None:
    init_config(facefusion.globals.config_path)
    values = parse_config()
    write_config(values)
