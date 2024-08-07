from typing import List, Optional, Tuple

import gradio

from facefusion import state_manager, wording
from facefusion.processors import choices as processors_choices
from facefusion.processors.core import load_processor_module
from facefusion.processors.typing import FaceEditorModel
from facefusion.uis.core import get_ui_component, register_ui_component

FACE_EDITOR_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_EDITOR_EYEBROW_DIRECTION_SLIDER : Optional[gradio.Slider] = None
FACE_EDITOR_EYE_GAZE_HORIZONTAL_SLIDER : Optional[gradio.Slider] = None
FACE_EDITOR_EYE_GAZE_VERTICAL_SLIDER : Optional[gradio.Slider] = None
FACE_EDITOR_EYE_OPEN_RATIO_SLIDER : Optional[gradio.Slider] = None
FACE_EDITOR_LIP_OPEN_RATIO_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global FACE_EDITOR_MODEL_DROPDOWN
	global FACE_EDITOR_EYEBROW_DIRECTION_SLIDER
	global FACE_EDITOR_EYE_GAZE_HORIZONTAL_SLIDER
	global FACE_EDITOR_EYE_GAZE_VERTICAL_SLIDER
	global FACE_EDITOR_EYE_OPEN_RATIO_SLIDER
	global FACE_EDITOR_LIP_OPEN_RATIO_SLIDER

	FACE_EDITOR_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.face_editor_model_dropdown'),
		choices = processors_choices.face_editor_models,
		value = state_manager.get_item('face_editor_model'),
		visible = 'face_editor' in state_manager.get_item('processors')
	)
	FACE_EDITOR_EYEBROW_DIRECTION_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_eyebrow_direction_slider'),
		value = state_manager.get_item('face_editor_eyebrow_direction'),
		step = processors_choices.face_editor_eyebrow_direction_range[1] - processors_choices.face_editor_eyebrow_direction_range[0],
		minimum = processors_choices.face_editor_eyebrow_direction_range[0],
		maximum = processors_choices.face_editor_eyebrow_direction_range[-1],
		visible = 'face_editor' in state_manager.get_item('processors'),
	)
	FACE_EDITOR_EYE_GAZE_HORIZONTAL_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_eye_gaze_horizontal_slider'),
		value = state_manager.get_item('face_editor_eye_gaze_horizontal'),
		step = processors_choices.face_editor_eye_gaze_horizontal_range[1] - processors_choices.face_editor_eye_gaze_horizontal_range[0],
		minimum = processors_choices.face_editor_eye_gaze_horizontal_range[0],
		maximum = processors_choices.face_editor_eye_gaze_horizontal_range[-1],
		visible = 'face_editor' in state_manager.get_item('processors'),
	)
	FACE_EDITOR_EYE_GAZE_VERTICAL_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_eye_gaze_vertical_slider'),
		value = state_manager.get_item('face_editor_eye_gaze_vertical'),
		step = processors_choices.face_editor_eye_gaze_vertical_range[1] - processors_choices.face_editor_eye_gaze_vertical_range[0],
		minimum = processors_choices.face_editor_eye_gaze_vertical_range[0],
		maximum = processors_choices.face_editor_eye_gaze_vertical_range[-1],
		visible = 'face_editor' in state_manager.get_item('processors'),
	)
	FACE_EDITOR_EYE_OPEN_RATIO_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_eye_open_ratio_slider'),
		value = state_manager.get_item('face_editor_eye_open_ratio'),
		step = processors_choices.face_editor_eye_open_ratio_range[1] - processors_choices.face_editor_eye_open_ratio_range[0],
		minimum = processors_choices.face_editor_eye_open_ratio_range[0],
		maximum = processors_choices.face_editor_eye_open_ratio_range[-1],
		visible = 'face_editor' in state_manager.get_item('processors'),
	)
	FACE_EDITOR_LIP_OPEN_RATIO_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_lip_open_ratio_slider'),
		value = state_manager.get_item('face_editor_lip_open_ratio'),
		step = processors_choices.face_editor_lip_open_ratio_range[1] - processors_choices.face_editor_lip_open_ratio_range[0],
		minimum = processors_choices.face_editor_lip_open_ratio_range[0],
		maximum = processors_choices.face_editor_lip_open_ratio_range[-1],
		visible = 'face_editor' in state_manager.get_item('processors'),
	)
	register_ui_component('face_editor_model_dropdown', FACE_EDITOR_MODEL_DROPDOWN)
	register_ui_component('face_editor_eyebrow_direction_slider', FACE_EDITOR_EYEBROW_DIRECTION_SLIDER)
	register_ui_component('face_editor_eye_gaze_horizontal_slider', FACE_EDITOR_EYE_GAZE_HORIZONTAL_SLIDER)
	register_ui_component('face_editor_eye_gaze_vertical_slider', FACE_EDITOR_EYE_GAZE_VERTICAL_SLIDER)
	register_ui_component('face_editor_eye_open_ratio_slider', FACE_EDITOR_EYE_OPEN_RATIO_SLIDER)
	register_ui_component('face_editor_lip_open_ratio_slider', FACE_EDITOR_LIP_OPEN_RATIO_SLIDER)


def listen() -> None:
	FACE_EDITOR_MODEL_DROPDOWN.change(update_face_editor_model, inputs = FACE_EDITOR_MODEL_DROPDOWN, outputs = FACE_EDITOR_MODEL_DROPDOWN)
	FACE_EDITOR_EYEBROW_DIRECTION_SLIDER.release(update_face_editor_eyebrow_direction, inputs = FACE_EDITOR_EYEBROW_DIRECTION_SLIDER)
	FACE_EDITOR_EYE_GAZE_HORIZONTAL_SLIDER.release(update_face_editor_eye_gaze_horizontal, inputs = FACE_EDITOR_EYE_GAZE_HORIZONTAL_SLIDER)
	FACE_EDITOR_EYE_GAZE_VERTICAL_SLIDER.release(update_face_editor_eye_gaze_vertical, inputs = FACE_EDITOR_EYE_GAZE_VERTICAL_SLIDER)
	FACE_EDITOR_EYE_OPEN_RATIO_SLIDER.release(update_face_editor_eye_open_ratio, inputs = FACE_EDITOR_EYE_OPEN_RATIO_SLIDER)
	FACE_EDITOR_LIP_OPEN_RATIO_SLIDER.release(update_face_editor_lip_open_ratio, inputs = FACE_EDITOR_LIP_OPEN_RATIO_SLIDER)

	processors_checkbox_group = get_ui_component('processors_checkbox_group')
	if processors_checkbox_group:
		processors_checkbox_group.change(remote_update, inputs = processors_checkbox_group, outputs = [ FACE_EDITOR_MODEL_DROPDOWN, FACE_EDITOR_EYEBROW_DIRECTION_SLIDER, FACE_EDITOR_EYE_GAZE_HORIZONTAL_SLIDER, FACE_EDITOR_EYE_GAZE_VERTICAL_SLIDER, FACE_EDITOR_EYE_OPEN_RATIO_SLIDER, FACE_EDITOR_LIP_OPEN_RATIO_SLIDER ])


def remote_update(processors : List[str]) -> Tuple[gradio.Dropdown, gradio.Slider, gradio.Slider, gradio.Slider, gradio.Slider, gradio.Slider]:
	has_face_editor = 'face_editor' in processors
	return gradio.Dropdown(visible = has_face_editor), gradio.Slider(visible = has_face_editor), gradio.Slider(visible = has_face_editor), gradio.Slider(visible = has_face_editor), gradio.Slider(visible = has_face_editor), gradio.Slider(visible = has_face_editor)


def update_face_editor_model(face_editor_model : FaceEditorModel) -> gradio.Dropdown:
	face_editor_module = load_processor_module('face_editor')
	face_editor_module.clear_inference_pool()
	state_manager.set_item('face_editor_model', face_editor_model)

	if face_editor_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('face_editor_model'))
	return gradio.Dropdown()


def update_face_editor_eyebrow_direction(face_editor_eyebrow_direction : float) -> None:
	state_manager.set_item('face_editor_eyebrow_direction', face_editor_eyebrow_direction)


def update_face_editor_eye_gaze_horizontal(face_editor_eye_gaze_horizontal : float) -> None:
	state_manager.set_item('face_editor_eye_gaze_horizontal', face_editor_eye_gaze_horizontal)


def update_face_editor_eye_gaze_vertical(face_editor_eye_gaze_vertical : float) -> None:
	state_manager.set_item('face_editor_eye_gaze_vertical', face_editor_eye_gaze_vertical)


def update_face_editor_eye_open_ratio(face_editor_eye_open_ratio : float) -> None:
	state_manager.set_item('face_editor_eye_open_ratio', face_editor_eye_open_ratio)


def update_face_editor_lip_open_ratio(face_editor_lip_open_ratio : float) -> None:
	state_manager.set_item('face_editor_lip_open_ratio', face_editor_lip_open_ratio)
