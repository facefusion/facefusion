from typing import List, Optional
import gradio

import facefusion.globals
from facefusion import wording
from facefusion.processors.frame.core import load_frame_processor_module, clear_frame_processors_modules
from facefusion.utilities import list_module_names
from facefusion.uis.core import register_ui_component

FRAME_PROCESSORS_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None


def render() -> None:
	global FRAME_PROCESSORS_CHECKBOX_GROUP

	FRAME_PROCESSORS_CHECKBOX_GROUP = gradio.CheckboxGroup(
		label = wording.get('frame_processors_checkbox_group_label'),
		choices = sort_frame_processors(facefusion.globals.frame_processors),
		value = facefusion.globals.frame_processors
	)
	register_ui_component('frame_processors_checkbox_group', FRAME_PROCESSORS_CHECKBOX_GROUP)


def listen() -> None:
	FRAME_PROCESSORS_CHECKBOX_GROUP.change(update_frame_processors, inputs = FRAME_PROCESSORS_CHECKBOX_GROUP, outputs = FRAME_PROCESSORS_CHECKBOX_GROUP)


def update_frame_processors(frame_processors : List[str]) -> gradio.CheckboxGroup:
	facefusion.globals.frame_processors = frame_processors
	clear_frame_processors_modules()
	for frame_processor in frame_processors:
		frame_processor_module = load_frame_processor_module(frame_processor)
		if not frame_processor_module.pre_check():
			return gradio.CheckboxGroup()
	return gradio.CheckboxGroup(value = frame_processors, choices = sort_frame_processors(frame_processors))


def sort_frame_processors(frame_processors : List[str]) -> list[str]:
	available_frame_processors = list_module_names('facefusion/processors/frame/modules')
	return sorted(available_frame_processors, key = lambda frame_processor : frame_processors.index(frame_processor) if frame_processor in frame_processors else len(frame_processors))
