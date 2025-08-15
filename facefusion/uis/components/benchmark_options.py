from typing import List, Optional

import gradio

import facefusion.choices
from facefusion import state_manager, wording
from facefusion.common_helper import calculate_int_step
from facefusion.types import BenchmarkMode, BenchmarkResolution

BENCHMARK_MODE_DROPDOWN : Optional[gradio.Dropdown] = None
BENCHMARK_RESOLUTIONS_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None
BENCHMARK_CYCLE_COUNT_SLIDER : Optional[gradio.Button] = None


def render() -> None:
	global BENCHMARK_MODE_DROPDOWN
	global BENCHMARK_RESOLUTIONS_CHECKBOX_GROUP
	global BENCHMARK_CYCLE_COUNT_SLIDER

	BENCHMARK_MODE_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.benchmark_mode_dropdown'),
		choices = facefusion.choices.benchmark_modes,
		value = state_manager.get_item('benchmark_mode')
	)
	BENCHMARK_RESOLUTIONS_CHECKBOX_GROUP = gradio.CheckboxGroup(
		label = wording.get('uis.benchmark_resolutions_checkbox_group'),
		choices = facefusion.choices.benchmark_resolutions,
		value = state_manager.get_item('benchmark_resolutions')
	)
	BENCHMARK_CYCLE_COUNT_SLIDER = gradio.Slider(
		label = wording.get('uis.benchmark_cycle_count_slider'),
		value = state_manager.get_item('benchmark_cycle_count'),
		step = calculate_int_step(facefusion.choices.benchmark_cycle_count_range),
		minimum = facefusion.choices.benchmark_cycle_count_range[0],
		maximum = facefusion.choices.benchmark_cycle_count_range[-1]
	)


def listen() -> None:
	BENCHMARK_MODE_DROPDOWN.change(update_benchmark_mode, inputs = BENCHMARK_MODE_DROPDOWN)
	BENCHMARK_RESOLUTIONS_CHECKBOX_GROUP.change(update_benchmark_resolutions, inputs = BENCHMARK_RESOLUTIONS_CHECKBOX_GROUP)
	BENCHMARK_CYCLE_COUNT_SLIDER.release(update_benchmark_cycle_count, inputs = BENCHMARK_CYCLE_COUNT_SLIDER)


def update_benchmark_mode(benchmark_mode : BenchmarkMode) -> None:
	state_manager.set_item('benchmark_mode', benchmark_mode)


def update_benchmark_resolutions(benchmark_resolutions : List[BenchmarkResolution]) -> None:
	state_manager.set_item('benchmark_resolutions', benchmark_resolutions)


def update_benchmark_cycle_count(benchmark_cycle_count : int) -> None:
	state_manager.set_item('benchmark_cycle_count', benchmark_cycle_count)
