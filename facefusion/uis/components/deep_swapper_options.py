from typing import List, Optional

import gradio

from facefusion import state_manager, wording
from facefusion.processors import choices as processors_choices
from facefusion.processors.core import load_processor_module
from facefusion.processors.typing import DeepSwapperModel
from facefusion.uis.core import get_ui_component, register_ui_component

DEEP_SWAPPER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None


def render() -> None:
	global DEEP_SWAPPER_MODEL_DROPDOWN

	DEEP_SWAPPER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.deep_swapper_model_dropdown'),
		choices = processors_choices.deep_swapper_models,
		value = state_manager.get_item('deep_swapper_model'),
		visible = 'deep_swapper' in state_manager.get_item('processors')
	)
	register_ui_component('deep_swapper_model_dropdown', DEEP_SWAPPER_MODEL_DROPDOWN)


def listen() -> None:
	DEEP_SWAPPER_MODEL_DROPDOWN.change(update_deep_swapper_model, inputs = DEEP_SWAPPER_MODEL_DROPDOWN, outputs = DEEP_SWAPPER_MODEL_DROPDOWN)

	processors_checkbox_group = get_ui_component('processors_checkbox_group')
	if processors_checkbox_group:
		processors_checkbox_group.change(remote_update, inputs = processors_checkbox_group, outputs = DEEP_SWAPPER_MODEL_DROPDOWN)


def remote_update(processors : List[str]) -> gradio.Dropdown:
	has_deep_swapper = 'deep_swapper' in processors
	return gradio.Dropdown(visible = has_deep_swapper)


def update_deep_swapper_model(deep_swapper_model : DeepSwapperModel) -> gradio.Dropdown:
	deep_swapper_module = load_processor_module('deep_swapper')
	deep_swapper_module.clear_inference_pool()
	state_manager.set_item('deep_swapper_model', deep_swapper_model)

	if deep_swapper_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('deep_swapper_model'))
	return gradio.Dropdown()
