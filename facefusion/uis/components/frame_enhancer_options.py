from typing import List, Optional, Tuple

import gradio

from facefusion import state_manager, wording
from facefusion.processors.frame import choices as frame_processors_choices
from facefusion.processors.frame.core import load_frame_processor_module
from facefusion.processors.frame.typing import FrameEnhancerModel
from facefusion.uis.core import get_ui_component, register_ui_component

FRAME_ENHANCER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
FRAME_ENHANCER_BLEND_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global FRAME_ENHANCER_MODEL_DROPDOWN
	global FRAME_ENHANCER_BLEND_SLIDER

	FRAME_ENHANCER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.frame_enhancer_model_dropdown'),
		choices = frame_processors_choices.frame_enhancer_models,
		value = state_manager.get_item('frame_enhancer_model'),
		visible = 'frame_enhancer' in state_manager.get_item('frame_processors')
	)
	FRAME_ENHANCER_BLEND_SLIDER = gradio.Slider(
		label = wording.get('uis.frame_enhancer_blend_slider'),
		value = state_manager.get_item('frame_enhancer_blend'),
		step = frame_processors_choices.frame_enhancer_blend_range[1] - frame_processors_choices.frame_enhancer_blend_range[0],
		minimum = frame_processors_choices.frame_enhancer_blend_range[0],
		maximum = frame_processors_choices.frame_enhancer_blend_range[-1],
		visible = 'frame_enhancer' in state_manager.get_item('frame_processors')
	)
	register_ui_component('frame_enhancer_model_dropdown', FRAME_ENHANCER_MODEL_DROPDOWN)
	register_ui_component('frame_enhancer_blend_slider', FRAME_ENHANCER_BLEND_SLIDER)


def listen() -> None:
	FRAME_ENHANCER_MODEL_DROPDOWN.change(update_frame_enhancer_model, inputs = FRAME_ENHANCER_MODEL_DROPDOWN, outputs = FRAME_ENHANCER_MODEL_DROPDOWN)
	FRAME_ENHANCER_BLEND_SLIDER.release(update_frame_enhancer_blend, inputs = FRAME_ENHANCER_BLEND_SLIDER)

	frame_processors_checkbox_group = get_ui_component('frame_processors_checkbox_group')
	if frame_processors_checkbox_group:
		frame_processors_checkbox_group.change(remote_update, inputs = frame_processors_checkbox_group, outputs = [ FRAME_ENHANCER_MODEL_DROPDOWN, FRAME_ENHANCER_BLEND_SLIDER ])


def remote_update(frame_processors : List[str]) -> Tuple[gradio.Dropdown, gradio.Slider]:
	has_frame_enhancer = 'frame_enhancer' in frame_processors
	return gradio.Dropdown(visible = has_frame_enhancer), gradio.Slider(visible = has_frame_enhancer)


def update_frame_enhancer_model(frame_enhancer_model : FrameEnhancerModel) -> gradio.Dropdown:
	frame_enhancer_module = load_frame_processor_module('frame_enhancer')
	frame_enhancer_module.clear_frame_processor()
	state_manager.set_item('frame_enhancer_model', frame_enhancer_model)
	frame_enhancer_module.set_options('model', frame_enhancer_module.MODELS[state_manager.get_item('frame_enhancer_model')])

	if frame_enhancer_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('frame_enhancer_model'))
	return gradio.Dropdown()


def update_frame_enhancer_blend(frame_enhancer_blend : float) -> None:
	state_manager.set_item('frame_enhancer_blend', int(frame_enhancer_blend))
