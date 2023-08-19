from typing import List, Optional
import gradio
import onnxruntime

import facefusion.globals
from facefusion import wording
from facefusion.face_analyser import clear_face_analyser
from facefusion.processors.frame.core import clear_frame_processors_modules
from facefusion.uis.typing import Update
from facefusion.utilities import encode_execution_providers, decode_execution_providers

EXECUTION_PROVIDERS_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None
EXECUTION_THREAD_COUNT_SLIDER : Optional[gradio.Slider] = None
EXECUTION_QUEUE_COUNT_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global EXECUTION_PROVIDERS_CHECKBOX_GROUP
	global EXECUTION_THREAD_COUNT_SLIDER
	global EXECUTION_QUEUE_COUNT_SLIDER

	with gradio.Box():
		EXECUTION_PROVIDERS_CHECKBOX_GROUP = gradio.CheckboxGroup(
			label = wording.get('execution_providers_checkbox_group_label'),
			choices = encode_execution_providers(onnxruntime.get_available_providers()),
			value = encode_execution_providers(facefusion.globals.execution_providers)
		)
		EXECUTION_THREAD_COUNT_SLIDER = gradio.Slider(
			label = wording.get('execution_thread_count_slider_label'),
			value = facefusion.globals.execution_thread_count,
			step = 1,
			minimum = 1,
			maximum = 128
		)
		EXECUTION_QUEUE_COUNT_SLIDER = gradio.Slider(
			label = wording.get('execution_queue_count_slider_label'),
			value = facefusion.globals.execution_queue_count,
			step = 1,
			minimum = 1,
			maximum = 16
		)


def listen() -> None:
	EXECUTION_PROVIDERS_CHECKBOX_GROUP.change(update_execution_providers, inputs = EXECUTION_PROVIDERS_CHECKBOX_GROUP, outputs = EXECUTION_PROVIDERS_CHECKBOX_GROUP)
	EXECUTION_THREAD_COUNT_SLIDER.change(update_execution_thread_count, inputs = EXECUTION_THREAD_COUNT_SLIDER, outputs = EXECUTION_THREAD_COUNT_SLIDER)
	EXECUTION_QUEUE_COUNT_SLIDER.change(update_execution_queue_count, inputs = EXECUTION_QUEUE_COUNT_SLIDER, outputs = EXECUTION_QUEUE_COUNT_SLIDER)


def update_execution_providers(execution_providers : List[str]) -> Update:
	clear_face_analyser()
	clear_frame_processors_modules()
	facefusion.globals.execution_providers = decode_execution_providers(execution_providers)
	return gradio.update(value = execution_providers)


def update_execution_thread_count(execution_thread_count : int = 1) -> Update:
	facefusion.globals.execution_thread_count = execution_thread_count
	return gradio.update(value = execution_thread_count)


def update_execution_queue_count(execution_queue_count : int = 1) -> Update:
	facefusion.globals.execution_queue_count = execution_queue_count
	return gradio.update(value = execution_queue_count)
