from typing import List, Optional

import gradio

from facefusion import state_manager, wording
from facefusion.filesystem import list_directory
from facefusion.processors.frame.core import clear_frame_processors_modules, load_frame_processor_module
from facefusion.uis.core import register_ui_component

FRAME_PROCESSORS_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None


def render() -> None:
	global FRAME_PROCESSORS_CHECKBOX_GROUP

	FRAME_PROCESSORS_CHECKBOX_GROUP = gradio.CheckboxGroup(
		label = wording.get('uis.frame_processors_checkbox_group'),
		choices = sort_frame_processors(state_manager.get_item('frame_processors')),
		value = state_manager.get_item('frame_processors')
	)
	register_ui_component('frame_processors_checkbox_group', FRAME_PROCESSORS_CHECKBOX_GROUP)


def listen() -> None:
	FRAME_PROCESSORS_CHECKBOX_GROUP.change(update_frame_processors, inputs = FRAME_PROCESSORS_CHECKBOX_GROUP, outputs = FRAME_PROCESSORS_CHECKBOX_GROUP)


def update_frame_processors(frame_processors : List[str]) -> gradio.CheckboxGroup:
	state_manager.set_item('frame_processors', frame_processors)
	clear_frame_processors_modules()
	for frame_processor in state_manager.get_item('frame_processors'):
		frame_processor_module = load_frame_processor_module(frame_processor)
		if not frame_processor_module.pre_check():
			return gradio.CheckboxGroup()
	return gradio.CheckboxGroup(value = state_manager.get_item('frame_processors'), choices = sort_frame_processors(state_manager.get_item('frame_processors')))


def sort_frame_processors(frame_processors : List[str]) -> List[str]:
	available_frame_processors = list_directory('facefusion/processors/frame/modules')
	return sorted(available_frame_processors, key = lambda frame_processor : frame_processors.index(frame_processor) if frame_processor in frame_processors else len(frame_processors))
