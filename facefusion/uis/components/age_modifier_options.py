from typing import List, Optional, Tuple

import gradio

from facefusion import state_manager, wording
from facefusion.processors.frame import choices as frame_processors_choices
from facefusion.processors.frame.core import load_frame_processor_module
from facefusion.processors.frame.typing import AgeModifierModel
from facefusion.uis.core import get_ui_component, register_ui_component

AGE_MODIFIER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
AGE_MODIFIER_DIRECTION_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global AGE_MODIFIER_MODEL_DROPDOWN
	global AGE_MODIFIER_DIRECTION_SLIDER

	AGE_MODIFIER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.age_modifier_model_dropdown'),
		choices = frame_processors_choices.age_modifier_models,
		value = state_manager.get_item('age_modifier_model'),
		visible = 'age_modifier' in state_manager.get_item('frame_processors')
	)
	AGE_MODIFIER_DIRECTION_SLIDER = gradio.Slider(
		label = wording.get('uis.age_modifier_direction_slider'),
		value = state_manager.get_item('age_modifier_direction'),
		step = frame_processors_choices.age_modifier_direction_range[1] - frame_processors_choices.age_modifier_direction_range[0],
		minimum = frame_processors_choices.age_modifier_direction_range[0],
		maximum = frame_processors_choices.age_modifier_direction_range[-1],
		visible = 'age_modifier' in state_manager.get_item('frame_processors')
	)
	register_ui_component('age_modifier_model_dropdown', AGE_MODIFIER_MODEL_DROPDOWN)
	register_ui_component('age_modifier_direction_slider', AGE_MODIFIER_DIRECTION_SLIDER)


def listen() -> None:
	AGE_MODIFIER_MODEL_DROPDOWN.change(update_age_modifier_model, inputs = AGE_MODIFIER_MODEL_DROPDOWN, outputs = AGE_MODIFIER_MODEL_DROPDOWN)
	AGE_MODIFIER_DIRECTION_SLIDER.release(update_age_modifier_direction, inputs = AGE_MODIFIER_DIRECTION_SLIDER)

	frame_processors_checkbox_group = get_ui_component('frame_processors_checkbox_group')
	if frame_processors_checkbox_group:
		frame_processors_checkbox_group.change(update_frame_processors, inputs = frame_processors_checkbox_group, outputs = [ AGE_MODIFIER_MODEL_DROPDOWN, AGE_MODIFIER_DIRECTION_SLIDER ])


def update_frame_processors(frame_processors : List[str]) -> Tuple[gradio.Dropdown, gradio.Slider]:
	has_age_modifier = 'age_modifier' in frame_processors
	return gradio.Dropdown(visible = has_age_modifier), gradio.Slider(visible = has_age_modifier)


def update_age_modifier_model(age_modifier_model : AgeModifierModel) -> gradio.Dropdown:
	state_manager.set_item('age_modifier_model', age_modifier_model)
	age_modifier_module = load_frame_processor_module('age_modifier')
	age_modifier_module.clear_frame_processor()
	age_modifier_module.set_options('model', age_modifier_module.MODELS[state_manager.get_item('age_modifier_model')])
	if age_modifier_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('age_modifier_model'))
	return gradio.Dropdown()


def update_age_modifier_direction(age_modifier_direction : float) -> None:
	state_manager.set_item('age_modifier_direction', int(age_modifier_direction))
