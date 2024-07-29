from typing import List, Optional

import gradio

from facefusion import state_manager, wording
from facefusion.filesystem import list_directory
from facefusion.processors.core import clear_processors_modules, load_processor_module
from facefusion.uis.core import register_ui_component

PROCESSORS_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None


def render() -> None:
	global PROCESSORS_CHECKBOX_GROUP

	PROCESSORS_CHECKBOX_GROUP = gradio.CheckboxGroup(
		label = wording.get('uis.processors_checkbox_group'),
		choices = sort_processors(state_manager.get_item('processors')),
		value = state_manager.get_item('processors')
	)
	register_ui_component('processors_checkbox_group', PROCESSORS_CHECKBOX_GROUP)


def listen() -> None:
	PROCESSORS_CHECKBOX_GROUP.change(update_processors, inputs = PROCESSORS_CHECKBOX_GROUP, outputs = PROCESSORS_CHECKBOX_GROUP)


def update_processors(processors : List[str]) -> gradio.CheckboxGroup:
	state_manager.set_item('processors', processors)
	clear_processors_modules()

	for processor in state_manager.get_item('processors'):
		processor_module = load_processor_module(processor)
		if not processor_module.conditional_download_sources():
			return gradio.CheckboxGroup()
	return gradio.CheckboxGroup(value = state_manager.get_item('processors'), choices = sort_processors(state_manager.get_item('processors')))


def sort_processors(processors : List[str]) -> List[str]:
	available_processors = list_directory('facefusion/processors/modules')
	return sorted(available_processors, key = lambda processor : processors.index(processor) if processor in processors else len(processors))
