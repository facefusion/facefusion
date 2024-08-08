from typing import Optional

import gradio

import facefusion.choices
from facefusion import state_manager, wording
from facefusion.common_helper import calc_int_step

EXECUTION_THREAD_COUNT_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global EXECUTION_THREAD_COUNT_SLIDER

	EXECUTION_THREAD_COUNT_SLIDER = gradio.Slider(
		label = wording.get('uis.execution_thread_count_slider'),
		value = state_manager.get_item('execution_thread_count'),
		step = calc_int_step(facefusion.choices.execution_thread_count_range),
		minimum = facefusion.choices.execution_thread_count_range[0],
		maximum = facefusion.choices.execution_thread_count_range[-1]
	)


def listen() -> None:
	EXECUTION_THREAD_COUNT_SLIDER.release(update_execution_thread_count, inputs = EXECUTION_THREAD_COUNT_SLIDER)


def update_execution_thread_count(execution_thread_count : float) -> None:
	state_manager.set_item('execution_thread_count', int(execution_thread_count))
