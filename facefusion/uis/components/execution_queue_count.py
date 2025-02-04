from typing import Optional
<<<<<<< HEAD
import gradio

import facefusion.globals
import facefusion.choices
from facefusion import wording
=======

import gradio

import facefusion.choices
from facefusion import state_manager, wording
from facefusion.common_helper import calc_int_step
>>>>>>> origin/master

EXECUTION_QUEUE_COUNT_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global EXECUTION_QUEUE_COUNT_SLIDER

	EXECUTION_QUEUE_COUNT_SLIDER = gradio.Slider(
		label = wording.get('uis.execution_queue_count_slider'),
<<<<<<< HEAD
		value = facefusion.globals.execution_queue_count,
		step = facefusion.choices.execution_queue_count_range[1] - facefusion.choices.execution_queue_count_range[0],
=======
		value = state_manager.get_item('execution_queue_count'),
		step = calc_int_step(facefusion.choices.execution_queue_count_range),
>>>>>>> origin/master
		minimum = facefusion.choices.execution_queue_count_range[0],
		maximum = facefusion.choices.execution_queue_count_range[-1]
	)


def listen() -> None:
	EXECUTION_QUEUE_COUNT_SLIDER.release(update_execution_queue_count, inputs = EXECUTION_QUEUE_COUNT_SLIDER)


<<<<<<< HEAD
def update_execution_queue_count(execution_queue_count : int = 1) -> None:
	facefusion.globals.execution_queue_count = execution_queue_count
=======
def update_execution_queue_count(execution_queue_count : float) -> None:
	state_manager.set_item('execution_queue_count', int(execution_queue_count))
>>>>>>> origin/master
