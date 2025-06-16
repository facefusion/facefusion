from typing import Optional

import gradio

import facefusion.choices
from facefusion import wording
from facefusion.uis.core import register_ui_component

BENCHMARK_RESOLUTIONS_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None
BENCHMARK_CYCLES_SLIDER : Optional[gradio.Button] = None


def render() -> None:
	global BENCHMARK_RESOLUTIONS_CHECKBOX_GROUP
	global BENCHMARK_CYCLES_SLIDER

	BENCHMARK_RESOLUTIONS_CHECKBOX_GROUP = gradio.CheckboxGroup(
		label = wording.get('uis.benchmark_resolutions_checkbox_group'),
		choices = facefusion.choices.benchmark_resolutions,
		value = facefusion.choices.benchmark_resolutions
	)
	BENCHMARK_CYCLES_SLIDER = gradio.Slider(
		label = wording.get('uis.benchmark_cycles_slider'),
		value = 5,
		step = 1,
		minimum = min(facefusion.choices.benchmark_cycles_range),
		maximum = max(facefusion.choices.benchmark_cycles_range)
	)
	register_ui_component('benchmark_resolutions_checkbox_group', BENCHMARK_RESOLUTIONS_CHECKBOX_GROUP)
	register_ui_component('benchmark_cycles_slider', BENCHMARK_CYCLES_SLIDER)
