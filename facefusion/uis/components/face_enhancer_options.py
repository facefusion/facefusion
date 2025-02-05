from typing import List, Optional, Tuple

import gradio

from facefusion import state_manager, wording
from facefusion.common_helper import calc_float_step, calc_int_step
from facefusion.processors import choices as processors_choices
from facefusion.processors.core import load_processor_module
from facefusion.processors.types import FaceEnhancerModel
from facefusion.uis.core import get_ui_component, register_ui_component

FACE_ENHANCER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_ENHANCER_BLEND_SLIDER : Optional[gradio.Slider] = None
FACE_ENHANCER_WEIGHT_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global FACE_ENHANCER_MODEL_DROPDOWN
	global FACE_ENHANCER_BLEND_SLIDER
	global FACE_ENHANCER_WEIGHT_SLIDER

	has_face_enhancer = 'face_enhancer' in state_manager.get_item('processors')
	FACE_ENHANCER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.face_enhancer_model_dropdown'),
		choices = processors_choices.face_enhancer_models,
		value = state_manager.get_item('face_enhancer_model'),
		visible = has_face_enhancer
	)
	FACE_ENHANCER_BLEND_SLIDER = gradio.Slider(
		label = wording.get('uis.face_enhancer_blend_slider'),
		value = state_manager.get_item('face_enhancer_blend'),
		step = calc_int_step(processors_choices.face_enhancer_blend_range),
		minimum = processors_choices.face_enhancer_blend_range[0],
		maximum = processors_choices.face_enhancer_blend_range[-1],
		visible = has_face_enhancer
	)
	FACE_ENHANCER_WEIGHT_SLIDER = gradio.Slider(
		label = wording.get('uis.face_enhancer_weight_slider'),
		value = state_manager.get_item('face_enhancer_weight'),
		step = calc_float_step(processors_choices.face_enhancer_weight_range),
		minimum = processors_choices.face_enhancer_weight_range[0],
		maximum = processors_choices.face_enhancer_weight_range[-1],
		visible = has_face_enhancer and load_processor_module('face_enhancer').get_inference_pool() and load_processor_module('face_enhancer').has_weight_input()
	)
	register_ui_component('face_enhancer_model_dropdown', FACE_ENHANCER_MODEL_DROPDOWN)
	register_ui_component('face_enhancer_blend_slider', FACE_ENHANCER_BLEND_SLIDER)
	register_ui_component('face_enhancer_weight_slider', FACE_ENHANCER_WEIGHT_SLIDER)


def listen() -> None:
	FACE_ENHANCER_MODEL_DROPDOWN.change(update_face_enhancer_model, inputs = FACE_ENHANCER_MODEL_DROPDOWN, outputs = [ FACE_ENHANCER_MODEL_DROPDOWN, FACE_ENHANCER_WEIGHT_SLIDER ])
	FACE_ENHANCER_BLEND_SLIDER.release(update_face_enhancer_blend, inputs = FACE_ENHANCER_BLEND_SLIDER)
	FACE_ENHANCER_WEIGHT_SLIDER.release(update_face_enhancer_weight, inputs = FACE_ENHANCER_WEIGHT_SLIDER)

	processors_checkbox_group = get_ui_component('processors_checkbox_group')
	if processors_checkbox_group:
		processors_checkbox_group.change(remote_update, inputs = processors_checkbox_group, outputs = [ FACE_ENHANCER_MODEL_DROPDOWN, FACE_ENHANCER_BLEND_SLIDER, FACE_ENHANCER_WEIGHT_SLIDER ])


def remote_update(processors : List[str]) -> Tuple[gradio.Dropdown, gradio.Slider, gradio.Slider]:
	has_face_enhancer = 'face_enhancer' in processors
	return gradio.Dropdown(visible = has_face_enhancer), gradio.Slider(visible = has_face_enhancer), gradio.Slider(visible = has_face_enhancer and load_processor_module('face_enhancer').get_inference_pool() and load_processor_module('face_enhancer').has_weight_input())


def update_face_enhancer_model(face_enhancer_model : FaceEnhancerModel) -> Tuple[gradio.Dropdown, gradio.Slider]:
	face_enhancer_module = load_processor_module('face_enhancer')
	face_enhancer_module.clear_inference_pool()
	state_manager.set_item('face_enhancer_model', face_enhancer_model)

	if face_enhancer_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('face_enhancer_model')), gradio.Slider(visible = face_enhancer_module.has_weight_input())
	return gradio.Dropdown(), gradio.Slider()


def update_face_enhancer_blend(face_enhancer_blend : float) -> None:
	state_manager.set_item('face_enhancer_blend', int(face_enhancer_blend))


def update_face_enhancer_weight(face_enhancer_weight : float) -> None:
	state_manager.set_item('face_enhancer_weight', face_enhancer_weight)

