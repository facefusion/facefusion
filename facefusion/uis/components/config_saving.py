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
from facefusion import wording

CONFIG_SAVE_BUTTON: Optional[gradio.Button] = None
CONFIG_SAVE_TEXTBOX: Optional[gradio.Textbox] = None


def render() -> None:
    global CONFIG_SAVE_TEXTBOX, CONFIG_SAVE_BUTTON
    CONFIG_SAVE_TEXTBOX = gradio.Textbox(label = 'ACTIVE CONFIG FILE',
                                         placeholder = facefusion.globals.config_path,
                                         max_lines = 1,
                                         interactive= False
                                         )
    CONFIG_SAVE_BUTTON = gradio.Button(value = 'SAVE PARAMETERS',
                                       variant = 'primary',
                                       size = 'sm')
    

def listen() -> None:
    CONFIG_SAVE_BUTTON.click(create_new_config_file)


def save_info(filepath: str)-> None:
    gradio.Info(wording.get('config_file_saved').format(filepath = filepath))


def create_new_config_file() -> None:
    modules = [facefusion.globals, facefusion.choices, frameglobals, framechoices]
    config = new_config(modules)
    with open(facefusion.globals.config_path, 'w') as configfile:
        config.write(configfile)
    save_info(facefusion.globals.config_path)


def new_config(modules: List[ModuleType]) -> ConfigParser:
    config = get_config()
    sections = {section: list(config[section].keys()) for section in config.sections()}
    for module in modules:
        for section, variables in sections.items():
            if section not in config:
                config[section] = {}
            for key in variables:
                try:
                    value = getattr(module, key)
                except AttributeError:
                    continue
                if value is not None:
                    if key == 'execution_providers':
                        value = ' '.join(encode_execution_providers(value))
                    config[section][key] = format_value(value)
                else:
                    config[section][key] = ''
    return config


def format_value(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return ' '.join(map(str, value))
    else:
        return str(value)