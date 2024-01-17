from typing import Optional
import gradio

import facefusion.globals
import facefusion.choices
from facefusion.typing import VideoMemoryStrategy
from facefusion import wording

VIDEO_MEMORY_STRATEGY : Optional[gradio.Dropdown] = None
MAX_MEMORY_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global VIDEO_MEMORY_STRATEGY
	global MAX_MEMORY_SLIDER

	VIDEO_MEMORY_STRATEGY = gradio.Dropdown(
		label = wording.get('video_memory_strategy_dropdown_label'),
		choices = facefusion.choices.video_memory_strategies,
		value = facefusion.globals.video_memory_strategy
	)
	MAX_MEMORY_SLIDER = gradio.Slider(
		label = wording.get('max_system_memory_slider_label'),
		step =facefusion.choices.max_system_memory_range[1] - facefusion.choices.max_system_memory_range[0],
		minimum = facefusion.choices.max_system_memory_range[0],
		maximum = facefusion.choices.max_system_memory_range[-1],
		value = facefusion.globals.max_system_memory
	)


def listen() -> None:
	VIDEO_MEMORY_STRATEGY.change(update_video_memory_strategy, inputs = VIDEO_MEMORY_STRATEGY)
	MAX_MEMORY_SLIDER.change(update_max_system_memory, inputs = MAX_MEMORY_SLIDER)


def update_video_memory_strategy(video_memory_strategy : VideoMemoryStrategy) -> None:
	facefusion.globals.video_memory_strategy = video_memory_strategy


def update_max_system_memory(max_system_memory : int) -> None:
	facefusion.globals.max_system_memory = max_system_memory
