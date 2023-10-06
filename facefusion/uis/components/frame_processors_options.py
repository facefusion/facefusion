from typing import List, Optional, Tuple
import gradio

import facefusion.globals
from facefusion import wording
from facefusion.processors.frame.core import load_frame_processor_module
from facefusion.processors.frame import globals as frame_processors_globals, choices as frame_processors_choices
from facefusion.uis.core import get_ui_component, register_ui_component

FACE_SWAPPER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_ENHANCER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_ENHANCER_BLEND_SLIDER : Optional[gradio.Slider] = None
FRAME_ENHANCER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
FRAME_ENHANCER_BLEND_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global FACE_SWAPPER_MODEL_DROPDOWN
	global FACE_ENHANCER_MODEL_DROPDOWN
	global FACE_ENHANCER_BLEND_SLIDER
	global FRAME_ENHANCER_MODEL_DROPDOWN
	global FRAME_ENHANCER_BLEND_SLIDER

	FACE_SWAPPER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('face_swapper_model_dropdown_label'),
		choices = frame_processors_choices.face_swapper_models,
		value = frame_processors_globals.face_swapper_model,
		visible = 'face_swapper' in facefusion.globals.frame_processors
	)
	FACE_ENHANCER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('face_enhancer_model_dropdown_label'),
		choices = frame_processors_choices.face_enhancer_models,
		value = frame_processors_globals.face_enhancer_model,
		visible = 'face_enhancer' in facefusion.globals.frame_processors
	)
	FACE_ENHANCER_BLEND_SLIDER = gradio.Slider(
		label = wording.get('face_enhancer_blend_slider_label'),
		value = frame_processors_globals.face_enhancer_blend,
		step = 1,
		minimum = 0,
		maximum = 100,
		visible = 'face_enhancer' in facefusion.globals.frame_processors
	)
	FRAME_ENHANCER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('frame_enhancer_model_dropdown_label'),
		choices = frame_processors_choices.frame_enhancer_models,
		value = frame_processors_globals.frame_enhancer_model,
		visible = 'frame_enhancer' in facefusion.globals.frame_processors
	)
	FRAME_ENHANCER_BLEND_SLIDER = gradio.Slider(
		label = wording.get('frame_enhancer_blend_slider_label'),
		value = frame_processors_globals.frame_enhancer_blend,
		step = 1,
		minimum = 0,
		maximum = 100,
		visible = 'face_enhancer' in facefusion.globals.frame_processors
	)
	register_ui_component('face_swapper_model_dropdown', FACE_SWAPPER_MODEL_DROPDOWN)
	register_ui_component('face_enhancer_model_dropdown', FACE_ENHANCER_MODEL_DROPDOWN)
	register_ui_component('face_enhancer_blend_slider', FACE_ENHANCER_BLEND_SLIDER)
	register_ui_component('frame_enhancer_model_dropdown', FRAME_ENHANCER_MODEL_DROPDOWN)
	register_ui_component('frame_enhancer_blend_slider', FRAME_ENHANCER_BLEND_SLIDER)


def listen() -> None:
	FACE_SWAPPER_MODEL_DROPDOWN.change(update_face_swapper_model, inputs = FACE_SWAPPER_MODEL_DROPDOWN, outputs = FACE_SWAPPER_MODEL_DROPDOWN)
	FACE_ENHANCER_MODEL_DROPDOWN.change(update_face_enhancer_model, inputs = FACE_ENHANCER_MODEL_DROPDOWN, outputs = FACE_ENHANCER_MODEL_DROPDOWN)
	FACE_ENHANCER_BLEND_SLIDER.change(update_face_enhancer_blend, inputs = FACE_ENHANCER_BLEND_SLIDER)
	FRAME_ENHANCER_MODEL_DROPDOWN.change(update_frame_enhancer_model, inputs = FRAME_ENHANCER_MODEL_DROPDOWN, outputs = FRAME_ENHANCER_MODEL_DROPDOWN)
	FRAME_ENHANCER_BLEND_SLIDER.change(update_frame_enhancer_blend, inputs = FRAME_ENHANCER_BLEND_SLIDER)
	frame_processors_checkbox_group = get_ui_component('frame_processors_checkbox_group')
	if frame_processors_checkbox_group:
		frame_processors_checkbox_group.change(toggle_face_swapper_model, inputs = frame_processors_checkbox_group, outputs = [ FACE_SWAPPER_MODEL_DROPDOWN, FACE_ENHANCER_MODEL_DROPDOWN, FACE_ENHANCER_BLEND_SLIDER, FRAME_ENHANCER_MODEL_DROPDOWN, FRAME_ENHANCER_BLEND_SLIDER ])


def update_face_swapper_model(face_swapper_model : str) -> gradio.Dropdown:
	frame_processors_globals.face_swapper_model = face_swapper_model
	face_swapper_module = load_frame_processor_module('face_swapper')
	face_swapper_module.clear_frame_processor()
	face_swapper_module.set_options('model', face_swapper_module.MODELS[face_swapper_model])
	if not face_swapper_module.pre_check():
		return gradio.Dropdown()
	return gradio.Dropdown(value = face_swapper_model)


def update_face_enhancer_model(face_enhancer_model : str) -> gradio.Dropdown:
	frame_processors_globals.face_enhancer_model = face_enhancer_model
	face_enhancer_module = load_frame_processor_module('face_enhancer')
	face_enhancer_module.clear_frame_processor()
	face_enhancer_module.set_options('model', face_enhancer_module.MODELS[face_enhancer_model])
	if not face_enhancer_module.pre_check():
		return gradio.Dropdown()
	return gradio.Dropdown(value = face_enhancer_model)


def update_face_enhancer_blend(face_enhancer_blend : int) -> None:
	frame_processors_globals.face_enhancer_blend = face_enhancer_blend


def update_frame_enhancer_model(frame_enhancer_model : str) -> gradio.Dropdown:
	frame_processors_globals.frame_enhancer_model = frame_enhancer_model
	frame_enhancer_module = load_frame_processor_module('frame_enhancer')
	frame_enhancer_module.clear_frame_processor()
	frame_enhancer_module.set_options('model', frame_enhancer_module.MODELS[frame_enhancer_model])
	if not frame_enhancer_module.pre_check():
		return gradio.Dropdown()
	return gradio.Dropdown(value = frame_enhancer_model)


def update_frame_enhancer_blend(frame_enhancer_blend : int) -> None:
	frame_processors_globals.frame_enhancer_blend = frame_enhancer_blend


def toggle_face_swapper_model(frame_processors : List[str]) -> Tuple[gradio.Dropdown, gradio.Dropdown, gradio.Slider, gradio.Dropdown, gradio.Slider]:
	has_face_swapper = 'face_swapper' in frame_processors
	has_face_enhancer = 'face_enhancer' in frame_processors
	has_frame_enhancer = 'frame_enhancer' in frame_processors
	return gradio.Dropdown(visible = has_face_swapper), gradio.Dropdown(visible = has_face_enhancer), gradio.Slider(visible = has_face_enhancer), gradio.Dropdown(visible = has_frame_enhancer), gradio.Slider(visible = has_frame_enhancer)
