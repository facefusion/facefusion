from typing import List, Optional, Tuple

import gradio

from facefusion import state_manager, wording
from facefusion.common_helper import calc_int_step
from facefusion.processors import choices as processors_choices
from facefusion.processors.core import load_processor_module
from facefusion.processors.types import DeepSwapperModel
from facefusion.uis.core import get_ui_component, register_ui_component

DEEP_SWAPPER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
DEEP_SWAPPER_MORPH_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global DEEP_SWAPPER_MODEL_DROPDOWN
	global DEEP_SWAPPER_MORPH_SLIDER

	has_deep_swapper = 'deep_swapper' in state_manager.get_item('processors')
	DEEP_SWAPPER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.deep_swapper_model_dropdown'),
		choices = processors_choices.deep_swapper_models,
		value = state_manager.get_item('deep_swapper_model'),
		visible = has_deep_swapper
	)
	DEEP_SWAPPER_MORPH_SLIDER = gradio.Slider(
		label = wording.get('uis.deep_swapper_morph_slider'),
		value = state_manager.get_item('deep_swapper_morph'),
		step = calc_int_step(processors_choices.deep_swapper_morph_range),
		minimum = processors_choices.deep_swapper_morph_range[0],
		maximum = processors_choices.deep_swapper_morph_range[-1],
		visible = has_deep_swapper and load_processor_module('deep_swapper').get_inference_pool() and load_processor_module('deep_swapper').has_morph_input()
	)
	register_ui_component('deep_swapper_model_dropdown', DEEP_SWAPPER_MODEL_DROPDOWN)
	register_ui_component('deep_swapper_morph_slider', DEEP_SWAPPER_MORPH_SLIDER)


def listen() -> None:
	DEEP_SWAPPER_MODEL_DROPDOWN.change(update_deep_swapper_model, inputs = DEEP_SWAPPER_MODEL_DROPDOWN, outputs = [ DEEP_SWAPPER_MODEL_DROPDOWN, DEEP_SWAPPER_MORPH_SLIDER ])
	DEEP_SWAPPER_MORPH_SLIDER.release(update_deep_swapper_morph, inputs = DEEP_SWAPPER_MORPH_SLIDER)

	processors_checkbox_group = get_ui_component('processors_checkbox_group')
	if processors_checkbox_group:
		processors_checkbox_group.change(remote_update, inputs = processors_checkbox_group, outputs = [ DEEP_SWAPPER_MODEL_DROPDOWN, DEEP_SWAPPER_MORPH_SLIDER ])


def remote_update(processors : List[str]) -> Tuple[gradio.Dropdown, gradio.Slider]:
	has_deep_swapper = 'deep_swapper' in processors
	return gradio.Dropdown(visible = has_deep_swapper), gradio.Slider(visible = has_deep_swapper and load_processor_module('deep_swapper').get_inference_pool() and load_processor_module('deep_swapper').has_morph_input())


def update_deep_swapper_model(deep_swapper_model : DeepSwapperModel) -> Tuple[gradio.Dropdown, gradio.Slider]:
	deep_swapper_module = load_processor_module('deep_swapper')
	deep_swapper_module.clear_inference_pool()
	state_manager.set_item('deep_swapper_model', deep_swapper_model)

	if deep_swapper_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('deep_swapper_model')), gradio.Slider(visible = deep_swapper_module.has_morph_input())
	return gradio.Dropdown(), gradio.Slider()


def update_deep_swapper_morph(deep_swapper_morph : int) -> None:
	state_manager.set_item('deep_swapper_morph', deep_swapper_morph)
