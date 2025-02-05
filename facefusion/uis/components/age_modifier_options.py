from typing import List, Optional, Tuple

import gradio

from facefusion import state_manager, wording
from facefusion.common_helper import calc_float_step
from facefusion.processors import choices as processors_choices
from facefusion.processors.core import load_processor_module
from facefusion.processors.types import AgeModifierModel
from facefusion.uis.core import get_ui_component, register_ui_component

AGE_MODIFIER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
AGE_MODIFIER_DIRECTION_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global AGE_MODIFIER_MODEL_DROPDOWN
	global AGE_MODIFIER_DIRECTION_SLIDER

	has_age_modifier = 'age_modifier' in state_manager.get_item('processors')
	AGE_MODIFIER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.age_modifier_model_dropdown'),
		choices = processors_choices.age_modifier_models,
		value = state_manager.get_item('age_modifier_model'),
		visible = has_age_modifier
	)
	AGE_MODIFIER_DIRECTION_SLIDER = gradio.Slider(
		label = wording.get('uis.age_modifier_direction_slider'),
		value = state_manager.get_item('age_modifier_direction'),
		step = calc_float_step(processors_choices.age_modifier_direction_range),
		minimum = processors_choices.age_modifier_direction_range[0],
		maximum = processors_choices.age_modifier_direction_range[-1],
		visible = has_age_modifier
	)
	register_ui_component('age_modifier_model_dropdown', AGE_MODIFIER_MODEL_DROPDOWN)
	register_ui_component('age_modifier_direction_slider', AGE_MODIFIER_DIRECTION_SLIDER)


def listen() -> None:
	AGE_MODIFIER_MODEL_DROPDOWN.change(update_age_modifier_model, inputs = AGE_MODIFIER_MODEL_DROPDOWN, outputs = AGE_MODIFIER_MODEL_DROPDOWN)
	AGE_MODIFIER_DIRECTION_SLIDER.release(update_age_modifier_direction, inputs = AGE_MODIFIER_DIRECTION_SLIDER)

	processors_checkbox_group = get_ui_component('processors_checkbox_group')
	if processors_checkbox_group:
		processors_checkbox_group.change(remote_update, inputs = processors_checkbox_group, outputs = [ AGE_MODIFIER_MODEL_DROPDOWN, AGE_MODIFIER_DIRECTION_SLIDER ])


def remote_update(processors : List[str]) -> Tuple[gradio.Dropdown, gradio.Slider]:
	has_age_modifier = 'age_modifier' in processors
	return gradio.Dropdown(visible = has_age_modifier), gradio.Slider(visible = has_age_modifier)


def update_age_modifier_model(age_modifier_model : AgeModifierModel) -> gradio.Dropdown:
	age_modifier_module = load_processor_module('age_modifier')
	age_modifier_module.clear_inference_pool()
	state_manager.set_item('age_modifier_model', age_modifier_model)

	if age_modifier_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('age_modifier_model'))
	return gradio.Dropdown()


def update_age_modifier_direction(age_modifier_direction : float) -> None:
	state_manager.set_item('age_modifier_direction', int(age_modifier_direction))
