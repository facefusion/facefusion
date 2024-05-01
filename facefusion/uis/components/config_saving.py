from typing import List, Optional, Any
import gradio
from configparser import ConfigParser
from types import ModuleType
import os
from facefusion.config import clear_config
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
    CONFIG_SAVE_TEXTBOX = gradio.Textbox(label = 'SAVE CONFIG FILE',
                                         placeholder = facefusion.globals.config_path,
                                         max_lines = 1
                                         )
    CONFIG_SAVE_BUTTON = gradio.Button(value = 'SAVE',
                                       variant = 'primary',
                                       size = 'sm')
    

def listen() -> None:
    CONFIG_SAVE_BUTTON.click(create_new_config_file,inputs = CONFIG_SAVE_TEXTBOX)
    CONFIG_SAVE_BUTTON.click(fn=clear_text, outputs=CONFIG_SAVE_TEXTBOX)
    CONFIG_SAVE_TEXTBOX.select(fn=clear_text, outputs=CONFIG_SAVE_TEXTBOX)


def clear_text() -> None:
    return gradio.update(value='')


def save_info(filepath: str)-> None:
    gradio.Info(wording.get('config_file_saved').format(filepath = filepath))


def create_new_config_file(filename: str) -> None:
    if not filename:
        filename = facefusion.globals.config_path
    if not filename.endswith('.ini'):
        filename = filename + '.ini'
    modules = [facefusion.globals, facefusion.choices, frameglobals, framechoices]
    main_dir = os.getcwd()
    filepath = os.path.join(main_dir, filename)
    config = new_config(modules)
    with open(filepath, 'w') as configfile:
        config.write(configfile)
    save_info(filepath)


def new_config(modules: List[ModuleType]) -> ConfigParser:
    clear_config()
    config = ConfigParser()
    config.read(facefusion.globals.config_path)
    sections = {section: list(config[section].keys()) for section in config.sections()}

    for module in modules:
        for section, variables in sections.items():
            if section not in config:
                config[section] = {}
            for key in variables:
                try:
                    value = getattr(module, key)
                except AttributeError:
                    continue  # Skip attributes not found in the module
                if value is not None:
                    if key == 'execution_providers':
                        value = ' '.join(encode_execution_providers(value))
                    config[section][key] = format_value(value)
                else:
                    config[section][key] = ''
    return config


def format_value(value: Any) -> str:
    if isinstance(value, list):
        return ' '.join(map(str, value))
        
    elif isinstance(value, tuple):
        return ' '.join(map(str, value))
    else:
        return str(value)