from typing import List, Optional, Any
import gradio
from configparser import ConfigParser
from types import ModuleType
from facefusion.config import get_config
from facefusion.execution import encode_execution_providers
import facefusion.globals
import facefusion.choices
import facefusion.processors.frame.globals as frameglobals
import facefusion.processors.frame.choices as framechoices

CONFIG_SAVE_BUTTON: Optional[gradio.Button] = None


def render() -> None:
    global CONFIG_SAVE_BUTTON
    CONFIG_SAVE_BUTTON = gradio.Button(value = 'SAVE PARAMETERS',
                                       variant = 'primary',
                                       size = 'sm')
    

def listen() -> None:
    CONFIG_SAVE_BUTTON.click(update_config)


def update_config() -> None:
    modules = [facefusion.globals, facefusion.choices, frameglobals, framechoices]
    config = get_values(modules)
    with open(facefusion.globals.config_path, 'w') as configfile:
        config.write(configfile)


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
