from typing import Optional
import gradio

import facefusion.globals
import facefusion.choices
from facefusion import wording

MAX_MEMORY_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global MAX_MEMORY_SLIDER

	MAX_MEMORY_SLIDER = gradio.Slider(
		label = wording.get('max_memory_slider_label'),
		step = facefusion.choices.max_memory_range[1] - facefusion.choices.max_memory_range[0],
		minimum = facefusion.choices.max_memory_range[0],
		maximum = facefusion.choices.max_memory_range[-1]
	)


def listen() -> None:
	MAX_MEMORY_SLIDER.change(update_max_memory, inputs = MAX_MEMORY_SLIDER)


def update_max_memory(max_memory : int) -> None:
	facefusion.globals.max_memory = max_memory if max_memory > 0 else None
