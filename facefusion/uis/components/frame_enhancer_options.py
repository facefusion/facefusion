from typing import List, Optional, Tuple

import gradio

from facefusion import state_manager, wording
from facefusion.common_helper import calc_int_step
from facefusion.processors import choices as processors_choices
from facefusion.processors.core import load_processor_module
from facefusion.processors.types import FrameEnhancerModel
from facefusion.uis.core import get_ui_component, register_ui_component

FRAME_ENHANCER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
FRAME_ENHANCER_BLEND_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global FRAME_ENHANCER_MODEL_DROPDOWN
	global FRAME_ENHANCER_BLEND_SLIDER

	has_frame_enhancer = 'frame_enhancer' in state_manager.get_item('processors')
	FRAME_ENHANCER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.frame_enhancer_model_dropdown'),
		choices = processors_choices.frame_enhancer_models,
		value = state_manager.get_item('frame_enhancer_model'),
		visible = has_frame_enhancer
	)
	FRAME_ENHANCER_BLEND_SLIDER = gradio.Slider(
		label = wording.get('uis.frame_enhancer_blend_slider'),
		value = state_manager.get_item('frame_enhancer_blend'),
		step = calc_int_step(processors_choices.frame_enhancer_blend_range),
		minimum = processors_choices.frame_enhancer_blend_range[0],
		maximum = processors_choices.frame_enhancer_blend_range[-1],
		visible = has_frame_enhancer
	)
	register_ui_component('frame_enhancer_model_dropdown', FRAME_ENHANCER_MODEL_DROPDOWN)
	register_ui_component('frame_enhancer_blend_slider', FRAME_ENHANCER_BLEND_SLIDER)


def listen() -> None:
	FRAME_ENHANCER_MODEL_DROPDOWN.change(update_frame_enhancer_model, inputs = FRAME_ENHANCER_MODEL_DROPDOWN, outputs = FRAME_ENHANCER_MODEL_DROPDOWN)
	FRAME_ENHANCER_BLEND_SLIDER.release(update_frame_enhancer_blend, inputs = FRAME_ENHANCER_BLEND_SLIDER)

	processors_checkbox_group = get_ui_component('processors_checkbox_group')
	if processors_checkbox_group:
		processors_checkbox_group.change(remote_update, inputs = processors_checkbox_group, outputs = [ FRAME_ENHANCER_MODEL_DROPDOWN, FRAME_ENHANCER_BLEND_SLIDER ])


def remote_update(processors : List[str]) -> Tuple[gradio.Dropdown, gradio.Slider]:
	has_frame_enhancer = 'frame_enhancer' in processors
	return gradio.Dropdown(visible = has_frame_enhancer), gradio.Slider(visible = has_frame_enhancer)


def update_frame_enhancer_model(frame_enhancer_model : FrameEnhancerModel) -> gradio.Dropdown:
	frame_enhancer_module = load_processor_module('frame_enhancer')
	frame_enhancer_module.clear_inference_pool()
	state_manager.set_item('frame_enhancer_model', frame_enhancer_model)

	if frame_enhancer_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('frame_enhancer_model'))
	return gradio.Dropdown()


def update_frame_enhancer_blend(frame_enhancer_blend : float) -> None:
	state_manager.set_item('frame_enhancer_blend', int(frame_enhancer_blend))
