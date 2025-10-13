from typing import List, Optional, Tuple

import gradio

from facefusion import state_manager, wording
from facefusion.processors import choices as processors_choices
from facefusion.processors.core import load_processor_module
from facefusion.processors.types import BackgroundRemoverModel
from facefusion.uis import choices as ui_choices
from facefusion.uis.core import get_ui_component, register_ui_component

BACKGROUND_REMOVER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
BACKGROUND_REMOVER_COLOR_DROPDOWN : Optional[gradio.Dropdown] = None


def render() -> None:
	global BACKGROUND_REMOVER_MODEL_DROPDOWN
	global BACKGROUND_REMOVER_COLOR_DROPDOWN

	has_background_remover = 'background_remover' in state_manager.get_item('processors')
	background_remover_colors = list(ui_choices.background_remover_colors.keys())
	BACKGROUND_REMOVER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.background_remover_model_dropdown'),
		choices = processors_choices.background_remover_models,
		value = state_manager.get_item('background_remover_model'),
		visible = has_background_remover
	)
	BACKGROUND_REMOVER_COLOR_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.background_remover_color_dropdown'),
		choices = background_remover_colors,
		value = background_remover_colors[1],
		visible = has_background_remover
	)
	register_ui_component('background_remover_model_dropdown', BACKGROUND_REMOVER_MODEL_DROPDOWN)
	register_ui_component('background_remover_color_dropdown', BACKGROUND_REMOVER_COLOR_DROPDOWN)


def listen() -> None:
	BACKGROUND_REMOVER_MODEL_DROPDOWN.change(update_background_remover_model, inputs = BACKGROUND_REMOVER_MODEL_DROPDOWN, outputs = BACKGROUND_REMOVER_MODEL_DROPDOWN)
	BACKGROUND_REMOVER_COLOR_DROPDOWN.change(update_background_remover_color, inputs = BACKGROUND_REMOVER_COLOR_DROPDOWN)

	processors_checkbox_group = get_ui_component('processors_checkbox_group')
	if processors_checkbox_group:
		processors_checkbox_group.change(remote_update, inputs = processors_checkbox_group, outputs = [ BACKGROUND_REMOVER_MODEL_DROPDOWN, BACKGROUND_REMOVER_COLOR_DROPDOWN ])


def remote_update(processors : List[str]) -> Tuple[gradio.Dropdown, gradio.Dropdown]:
	has_background_remover = 'background_remover' in processors
	return gradio.Dropdown(visible = has_background_remover), gradio.Dropdown(visible = has_background_remover)


def update_background_remover_model(background_remover_model : BackgroundRemoverModel) -> gradio.Dropdown:
	background_remover_module = load_processor_module('background_remover')
	background_remover_module.clear_inference_pool()
	state_manager.set_item('background_remover_model', background_remover_model)

	if background_remover_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('background_remover_model'))
	return gradio.Dropdown()


def update_background_remover_color(background_remover_color : str) -> None:
	state_manager.set_item('background_remover_color', ui_choices.background_remover_colors.get(background_remover_color))
