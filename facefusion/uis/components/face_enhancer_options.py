from typing import List, Optional, Tuple

import gradio

from facefusion import state_manager, wording
from facefusion.processors.frame import choices as frame_processors_choices
from facefusion.processors.frame.core import load_frame_processor_module
from facefusion.processors.frame.typing import FaceEnhancerModel
from facefusion.uis.core import get_ui_component, register_ui_component

FACE_ENHANCER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_ENHANCER_BLEND_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global FACE_ENHANCER_MODEL_DROPDOWN
	global FACE_ENHANCER_BLEND_SLIDER

	FACE_ENHANCER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.face_enhancer_model_dropdown'),
		choices = frame_processors_choices.face_enhancer_models,
		value = state_manager.get_item('face_enhancer_model'),
		visible = 'face_enhancer' in state_manager.get_item('frame_processors')
	)
	FACE_ENHANCER_BLEND_SLIDER = gradio.Slider(
		label = wording.get('uis.face_enhancer_blend_slider'),
		value = state_manager.get_item('face_enhancer_blend'),
		step = frame_processors_choices.face_enhancer_blend_range[1] - frame_processors_choices.face_enhancer_blend_range[0],
		minimum = frame_processors_choices.face_enhancer_blend_range[0],
		maximum = frame_processors_choices.face_enhancer_blend_range[-1],
		visible = 'face_enhancer' in state_manager.get_item('frame_processors')
	)
	register_ui_component('face_enhancer_model_dropdown', FACE_ENHANCER_MODEL_DROPDOWN)
	register_ui_component('face_enhancer_blend_slider', FACE_ENHANCER_BLEND_SLIDER)


def listen() -> None:
	FACE_ENHANCER_MODEL_DROPDOWN.change(update_face_enhancer_model, inputs = FACE_ENHANCER_MODEL_DROPDOWN, outputs = FACE_ENHANCER_MODEL_DROPDOWN)

	frame_processors_checkbox_group = get_ui_component('frame_processors_checkbox_group')
	if frame_processors_checkbox_group:
		frame_processors_checkbox_group.change(remote_update, inputs = frame_processors_checkbox_group, outputs = [ FACE_ENHANCER_MODEL_DROPDOWN, FACE_ENHANCER_BLEND_SLIDER ])


def remote_update(frame_processors : List[str]) -> Tuple[gradio.Dropdown, gradio.Slider]:
	has_face_enhancer = 'face_enhancer' in frame_processors
	return gradio.Dropdown(visible = has_face_enhancer), gradio.Slider(visible = has_face_enhancer)


def update_face_enhancer_model(face_enhancer_model : FaceEnhancerModel) -> gradio.Dropdown:
	face_enhancer_module = load_frame_processor_module('face_enhancer')
	face_enhancer_module.clear_frame_processor()
	state_manager.set_item('face_enhancer_model', face_enhancer_model)
	face_enhancer_module.set_options('model', face_enhancer_module.MODELS[state_manager.get_item('face_enhancer_model')])

	if face_enhancer_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('face_enhancer_model'))
	return gradio.Dropdown()


def update_face_enhancer_blend(face_enhancer_blend : float) -> None:
	state_manager.set_item('face_enhancer_blend', int(face_enhancer_blend))
