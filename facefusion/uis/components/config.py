from typing import Optional
import gradio
from facefusion.processors.frame.config import save_config


CONFIG_SAVE_BUTTON: Optional[gradio.Button] = None


def render() -> None:
    global CONFIG_SAVE_BUTTON
    CONFIG_SAVE_BUTTON = gradio.Button(value = 'SAVE PARAMETERS',
                                       variant = 'primary',
                                       size = 'sm')
    

def listen() -> None:
    CONFIG_SAVE_BUTTON.click(save_config)
