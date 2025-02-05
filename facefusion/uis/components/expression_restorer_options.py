from typing import List, Optional, Tuple

import gradio

from facefusion import state_manager, wording
from facefusion.common_helper import calc_float_step
from facefusion.processors import choices as processors_choices
from facefusion.processors.core import load_processor_module
from facefusion.processors.types import ExpressionRestorerModel
from facefusion.uis.core import get_ui_component, register_ui_component

EXPRESSION_RESTORER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
EXPRESSION_RESTORER_FACTOR_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global EXPRESSION_RESTORER_MODEL_DROPDOWN
	global EXPRESSION_RESTORER_FACTOR_SLIDER

	has_expression_restorer = 'expression_restorer' in state_manager.get_item('processors')
	EXPRESSION_RESTORER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.expression_restorer_model_dropdown'),
		choices = processors_choices.expression_restorer_models,
		value = state_manager.get_item('expression_restorer_model'),
		visible = has_expression_restorer
	)
	EXPRESSION_RESTORER_FACTOR_SLIDER = gradio.Slider(
		label = wording.get('uis.expression_restorer_factor_slider'),
		value = state_manager.get_item('expression_restorer_factor'),
		step = calc_float_step(processors_choices.expression_restorer_factor_range),
		minimum = processors_choices.expression_restorer_factor_range[0],
		maximum = processors_choices.expression_restorer_factor_range[-1],
		visible = has_expression_restorer
	)
	register_ui_component('expression_restorer_model_dropdown', EXPRESSION_RESTORER_MODEL_DROPDOWN)
	register_ui_component('expression_restorer_factor_slider', EXPRESSION_RESTORER_FACTOR_SLIDER)


def listen() -> None:
	EXPRESSION_RESTORER_MODEL_DROPDOWN.change(update_expression_restorer_model, inputs = EXPRESSION_RESTORER_MODEL_DROPDOWN, outputs = EXPRESSION_RESTORER_MODEL_DROPDOWN)
	EXPRESSION_RESTORER_FACTOR_SLIDER.release(update_expression_restorer_factor, inputs = EXPRESSION_RESTORER_FACTOR_SLIDER)

	processors_checkbox_group = get_ui_component('processors_checkbox_group')
	if processors_checkbox_group:
		processors_checkbox_group.change(remote_update, inputs = processors_checkbox_group, outputs = [ EXPRESSION_RESTORER_MODEL_DROPDOWN, EXPRESSION_RESTORER_FACTOR_SLIDER ])


def remote_update(processors : List[str]) -> Tuple[gradio.Dropdown, gradio.Slider]:
	has_expression_restorer = 'expression_restorer' in processors
	return gradio.Dropdown(visible = has_expression_restorer), gradio.Slider(visible = has_expression_restorer)


def update_expression_restorer_model(expression_restorer_model : ExpressionRestorerModel) -> gradio.Dropdown:
	expression_restorer_module = load_processor_module('expression_restorer')
	expression_restorer_module.clear_inference_pool()
	state_manager.set_item('expression_restorer_model', expression_restorer_model)

	if expression_restorer_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('expression_restorer_model'))
	return gradio.Dropdown()


def update_expression_restorer_factor(expression_restorer_factor : float) -> None:
	state_manager.set_item('expression_restorer_factor', int(expression_restorer_factor))
