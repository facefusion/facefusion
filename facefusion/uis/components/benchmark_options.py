from typing import Optional
import gradio

from facefusion import wording
from facefusion.uis.core import register_ui_component
from facefusion.uis.components.benchmark import BENCHMARKS

BENCHMARK_RUNS_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None
BENCHMARK_CYCLES_SLIDER : Optional[gradio.Button] = None


def render() -> None:
	global BENCHMARK_RUNS_CHECKBOX_GROUP
	global BENCHMARK_CYCLES_SLIDER

	BENCHMARK_RUNS_CHECKBOX_GROUP = gradio.CheckboxGroup(
		label = wording.get('uis.benchmark_runs_checkbox_group'),
		value = list(BENCHMARKS.keys()),
		choices = list(BENCHMARKS.keys())
	)
	BENCHMARK_CYCLES_SLIDER = gradio.Slider(
		label = wording.get('uis.benchmark_cycles_slider'),
		value = 5,
		step = 1,
		minimum = 1,
		maximum = 10
	)
	register_ui_component('benchmark_runs_checkbox_group', BENCHMARK_RUNS_CHECKBOX_GROUP)
	register_ui_component('benchmark_cycles_slider', BENCHMARK_CYCLES_SLIDER)
