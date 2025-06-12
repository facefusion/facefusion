from typing import List, Optional, Tuple

import gradio

from facefusion import state_manager, wording
from facefusion.common_helper import calc_float_step
from facefusion.processors import choices as processors_choices
from facefusion.processors.core import load_processor_module
from facefusion.processors.types import FaceEditorModel
from facefusion.uis.core import get_ui_component, register_ui_component

FACE_EDITOR_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_EDITOR_EYEBROW_DIRECTION_SLIDER : Optional[gradio.Slider] = None
FACE_EDITOR_EYE_GAZE_HORIZONTAL_SLIDER : Optional[gradio.Slider] = None
FACE_EDITOR_EYE_GAZE_VERTICAL_SLIDER : Optional[gradio.Slider] = None
FACE_EDITOR_EYE_OPEN_RATIO_SLIDER : Optional[gradio.Slider] = None
FACE_EDITOR_LIP_OPEN_RATIO_SLIDER : Optional[gradio.Slider] = None
FACE_EDITOR_MOUTH_GRIM_SLIDER : Optional[gradio.Slider] = None
FACE_EDITOR_MOUTH_POUT_SLIDER : Optional[gradio.Slider] = None
FACE_EDITOR_MOUTH_PURSE_SLIDER : Optional[gradio.Slider] = None
FACE_EDITOR_MOUTH_SMILE_SLIDER : Optional[gradio.Slider] = None
FACE_EDITOR_MOUTH_POSITION_HORIZONTAL_SLIDER : Optional[gradio.Slider] = None
FACE_EDITOR_MOUTH_POSITION_VERTICAL_SLIDER : Optional[gradio.Slider] = None
FACE_EDITOR_HEAD_PITCH_SLIDER : Optional[gradio.Slider] = None
FACE_EDITOR_HEAD_YAW_SLIDER : Optional[gradio.Slider] = None
FACE_EDITOR_HEAD_ROLL_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global FACE_EDITOR_MODEL_DROPDOWN
	global FACE_EDITOR_EYEBROW_DIRECTION_SLIDER
	global FACE_EDITOR_EYE_GAZE_HORIZONTAL_SLIDER
	global FACE_EDITOR_EYE_GAZE_VERTICAL_SLIDER
	global FACE_EDITOR_EYE_OPEN_RATIO_SLIDER
	global FACE_EDITOR_LIP_OPEN_RATIO_SLIDER
	global FACE_EDITOR_MOUTH_GRIM_SLIDER
	global FACE_EDITOR_MOUTH_POUT_SLIDER
	global FACE_EDITOR_MOUTH_PURSE_SLIDER
	global FACE_EDITOR_MOUTH_SMILE_SLIDER
	global FACE_EDITOR_MOUTH_POSITION_HORIZONTAL_SLIDER
	global FACE_EDITOR_MOUTH_POSITION_VERTICAL_SLIDER
	global FACE_EDITOR_HEAD_PITCH_SLIDER
	global FACE_EDITOR_HEAD_YAW_SLIDER
	global FACE_EDITOR_HEAD_ROLL_SLIDER

	has_face_editor = 'face_editor' in state_manager.get_item('processors')
	FACE_EDITOR_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.face_editor_model_dropdown'),
		choices = processors_choices.face_editor_models,
		value = state_manager.get_item('face_editor_model'),
		visible = has_face_editor
	)
	FACE_EDITOR_EYEBROW_DIRECTION_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_eyebrow_direction_slider'),
		value = state_manager.get_item('face_editor_eyebrow_direction'),
		step = calc_float_step(processors_choices.face_editor_eyebrow_direction_range),
		minimum = processors_choices.face_editor_eyebrow_direction_range[0],
		maximum = processors_choices.face_editor_eyebrow_direction_range[-1],
		visible = has_face_editor
	)
	FACE_EDITOR_EYE_GAZE_HORIZONTAL_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_eye_gaze_horizontal_slider'),
		value = state_manager.get_item('face_editor_eye_gaze_horizontal'),
		step = calc_float_step(processors_choices.face_editor_eye_gaze_horizontal_range),
		minimum = processors_choices.face_editor_eye_gaze_horizontal_range[0],
		maximum = processors_choices.face_editor_eye_gaze_horizontal_range[-1],
		visible = has_face_editor
	)
	FACE_EDITOR_EYE_GAZE_VERTICAL_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_eye_gaze_vertical_slider'),
		value = state_manager.get_item('face_editor_eye_gaze_vertical'),
		step = calc_float_step(processors_choices.face_editor_eye_gaze_vertical_range),
		minimum = processors_choices.face_editor_eye_gaze_vertical_range[0],
		maximum = processors_choices.face_editor_eye_gaze_vertical_range[-1],
		visible = has_face_editor
	)
	FACE_EDITOR_EYE_OPEN_RATIO_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_eye_open_ratio_slider'),
		value = state_manager.get_item('face_editor_eye_open_ratio'),
		step = calc_float_step(processors_choices.face_editor_eye_open_ratio_range),
		minimum = processors_choices.face_editor_eye_open_ratio_range[0],
		maximum = processors_choices.face_editor_eye_open_ratio_range[-1],
		visible = has_face_editor
	)
	FACE_EDITOR_LIP_OPEN_RATIO_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_lip_open_ratio_slider'),
		value = state_manager.get_item('face_editor_lip_open_ratio'),
		step = calc_float_step(processors_choices.face_editor_lip_open_ratio_range),
		minimum = processors_choices.face_editor_lip_open_ratio_range[0],
		maximum = processors_choices.face_editor_lip_open_ratio_range[-1],
		visible = has_face_editor
	)
	FACE_EDITOR_MOUTH_GRIM_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_mouth_grim_slider'),
		value = state_manager.get_item('face_editor_mouth_grim'),
		step = calc_float_step(processors_choices.face_editor_mouth_grim_range),
		minimum = processors_choices.face_editor_mouth_grim_range[0],
		maximum = processors_choices.face_editor_mouth_grim_range[-1],
		visible = has_face_editor
	)
	FACE_EDITOR_MOUTH_POUT_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_mouth_pout_slider'),
		value = state_manager.get_item('face_editor_mouth_pout'),
		step = calc_float_step(processors_choices.face_editor_mouth_pout_range),
		minimum = processors_choices.face_editor_mouth_pout_range[0],
		maximum = processors_choices.face_editor_mouth_pout_range[-1],
		visible = has_face_editor
	)
	FACE_EDITOR_MOUTH_PURSE_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_mouth_purse_slider'),
		value = state_manager.get_item('face_editor_mouth_purse'),
		step = calc_float_step(processors_choices.face_editor_mouth_purse_range),
		minimum = processors_choices.face_editor_mouth_purse_range[0],
		maximum = processors_choices.face_editor_mouth_purse_range[-1],
		visible = has_face_editor
	)
	FACE_EDITOR_MOUTH_SMILE_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_mouth_smile_slider'),
		value = state_manager.get_item('face_editor_mouth_smile'),
		step = calc_float_step(processors_choices.face_editor_mouth_smile_range),
		minimum = processors_choices.face_editor_mouth_smile_range[0],
		maximum = processors_choices.face_editor_mouth_smile_range[-1],
		visible = has_face_editor
	)
	FACE_EDITOR_MOUTH_POSITION_HORIZONTAL_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_mouth_position_horizontal_slider'),
		value = state_manager.get_item('face_editor_mouth_position_horizontal'),
		step = calc_float_step(processors_choices.face_editor_mouth_position_horizontal_range),
		minimum = processors_choices.face_editor_mouth_position_horizontal_range[0],
		maximum = processors_choices.face_editor_mouth_position_horizontal_range[-1],
		visible = has_face_editor
	)
	FACE_EDITOR_MOUTH_POSITION_VERTICAL_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_mouth_position_vertical_slider'),
		value = state_manager.get_item('face_editor_mouth_position_vertical'),
		step = calc_float_step(processors_choices.face_editor_mouth_position_vertical_range),
		minimum = processors_choices.face_editor_mouth_position_vertical_range[0],
		maximum = processors_choices.face_editor_mouth_position_vertical_range[-1],
		visible = has_face_editor
	)
	FACE_EDITOR_HEAD_PITCH_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_head_pitch_slider'),
		value = state_manager.get_item('face_editor_head_pitch'),
		step = calc_float_step(processors_choices.face_editor_head_pitch_range),
		minimum = processors_choices.face_editor_head_pitch_range[0],
		maximum = processors_choices.face_editor_head_pitch_range[-1],
		visible = has_face_editor
	)
	FACE_EDITOR_HEAD_YAW_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_head_yaw_slider'),
		value = state_manager.get_item('face_editor_head_yaw'),
		step = calc_float_step(processors_choices.face_editor_head_yaw_range),
		minimum = processors_choices.face_editor_head_yaw_range[0],
		maximum = processors_choices.face_editor_head_yaw_range[-1],
		visible = has_face_editor
	)
	FACE_EDITOR_HEAD_ROLL_SLIDER = gradio.Slider(
		label = wording.get('uis.face_editor_head_roll_slider'),
		value = state_manager.get_item('face_editor_head_roll'),
		step = calc_float_step(processors_choices.face_editor_head_roll_range),
		minimum = processors_choices.face_editor_head_roll_range[0],
		maximum = processors_choices.face_editor_head_roll_range[-1],
		visible = has_face_editor
	)
	register_ui_component('face_editor_model_dropdown', FACE_EDITOR_MODEL_DROPDOWN)
	register_ui_component('face_editor_eyebrow_direction_slider', FACE_EDITOR_EYEBROW_DIRECTION_SLIDER)
	register_ui_component('face_editor_eye_gaze_horizontal_slider', FACE_EDITOR_EYE_GAZE_HORIZONTAL_SLIDER)
	register_ui_component('face_editor_eye_gaze_vertical_slider', FACE_EDITOR_EYE_GAZE_VERTICAL_SLIDER)
	register_ui_component('face_editor_eye_open_ratio_slider', FACE_EDITOR_EYE_OPEN_RATIO_SLIDER)
	register_ui_component('face_editor_lip_open_ratio_slider', FACE_EDITOR_LIP_OPEN_RATIO_SLIDER)
	register_ui_component('face_editor_mouth_grim_slider', FACE_EDITOR_MOUTH_GRIM_SLIDER)
	register_ui_component('face_editor_mouth_pout_slider', FACE_EDITOR_MOUTH_POUT_SLIDER)
	register_ui_component('face_editor_mouth_purse_slider', FACE_EDITOR_MOUTH_PURSE_SLIDER)
	register_ui_component('face_editor_mouth_smile_slider', FACE_EDITOR_MOUTH_SMILE_SLIDER)
	register_ui_component('face_editor_mouth_position_horizontal_slider', FACE_EDITOR_MOUTH_POSITION_HORIZONTAL_SLIDER)
	register_ui_component('face_editor_mouth_position_vertical_slider', FACE_EDITOR_MOUTH_POSITION_VERTICAL_SLIDER)
	register_ui_component('face_editor_head_pitch_slider', FACE_EDITOR_HEAD_PITCH_SLIDER)
	register_ui_component('face_editor_head_yaw_slider', FACE_EDITOR_HEAD_YAW_SLIDER)
	register_ui_component('face_editor_head_roll_slider', FACE_EDITOR_HEAD_ROLL_SLIDER)


def listen() -> None:
	FACE_EDITOR_MODEL_DROPDOWN.change(update_face_editor_model, inputs = FACE_EDITOR_MODEL_DROPDOWN, outputs = FACE_EDITOR_MODEL_DROPDOWN)
	FACE_EDITOR_EYEBROW_DIRECTION_SLIDER.release(update_face_editor_eyebrow_direction, inputs = FACE_EDITOR_EYEBROW_DIRECTION_SLIDER)
	FACE_EDITOR_EYE_GAZE_HORIZONTAL_SLIDER.release(update_face_editor_eye_gaze_horizontal, inputs = FACE_EDITOR_EYE_GAZE_HORIZONTAL_SLIDER)
	FACE_EDITOR_EYE_GAZE_VERTICAL_SLIDER.release(update_face_editor_eye_gaze_vertical, inputs = FACE_EDITOR_EYE_GAZE_VERTICAL_SLIDER)
	FACE_EDITOR_EYE_OPEN_RATIO_SLIDER.release(update_face_editor_eye_open_ratio, inputs = FACE_EDITOR_EYE_OPEN_RATIO_SLIDER)
	FACE_EDITOR_LIP_OPEN_RATIO_SLIDER.release(update_face_editor_lip_open_ratio, inputs = FACE_EDITOR_LIP_OPEN_RATIO_SLIDER)
	FACE_EDITOR_MOUTH_GRIM_SLIDER.release(update_face_editor_mouth_grim, inputs = FACE_EDITOR_MOUTH_GRIM_SLIDER)
	FACE_EDITOR_MOUTH_POUT_SLIDER.release(update_face_editor_mouth_pout, inputs = FACE_EDITOR_MOUTH_POUT_SLIDER)
	FACE_EDITOR_MOUTH_PURSE_SLIDER.release(update_face_editor_mouth_purse, inputs = FACE_EDITOR_MOUTH_PURSE_SLIDER)
	FACE_EDITOR_MOUTH_SMILE_SLIDER.release(update_face_editor_mouth_smile, inputs = FACE_EDITOR_MOUTH_SMILE_SLIDER)
	FACE_EDITOR_MOUTH_POSITION_HORIZONTAL_SLIDER.release(update_face_editor_mouth_position_horizontal, inputs = FACE_EDITOR_MOUTH_POSITION_HORIZONTAL_SLIDER)
	FACE_EDITOR_MOUTH_POSITION_VERTICAL_SLIDER.release(update_face_editor_mouth_position_vertical, inputs = FACE_EDITOR_MOUTH_POSITION_VERTICAL_SLIDER)
	FACE_EDITOR_HEAD_PITCH_SLIDER.release(update_face_editor_head_pitch, inputs = FACE_EDITOR_HEAD_PITCH_SLIDER)
	FACE_EDITOR_HEAD_YAW_SLIDER.release(update_face_editor_head_yaw, inputs = FACE_EDITOR_HEAD_YAW_SLIDER)
	FACE_EDITOR_HEAD_ROLL_SLIDER.release(update_face_editor_head_roll, inputs = FACE_EDITOR_HEAD_ROLL_SLIDER)

	processors_checkbox_group = get_ui_component('processors_checkbox_group')
	if processors_checkbox_group:
		processors_checkbox_group.change(remote_update, inputs = processors_checkbox_group, outputs = [ FACE_EDITOR_MODEL_DROPDOWN, FACE_EDITOR_EYEBROW_DIRECTION_SLIDER, FACE_EDITOR_EYE_GAZE_HORIZONTAL_SLIDER, FACE_EDITOR_EYE_GAZE_VERTICAL_SLIDER, FACE_EDITOR_EYE_OPEN_RATIO_SLIDER, FACE_EDITOR_LIP_OPEN_RATIO_SLIDER, FACE_EDITOR_MOUTH_GRIM_SLIDER, FACE_EDITOR_MOUTH_POUT_SLIDER, FACE_EDITOR_MOUTH_PURSE_SLIDER, FACE_EDITOR_MOUTH_SMILE_SLIDER, FACE_EDITOR_MOUTH_POSITION_HORIZONTAL_SLIDER, FACE_EDITOR_MOUTH_POSITION_VERTICAL_SLIDER, FACE_EDITOR_HEAD_PITCH_SLIDER, FACE_EDITOR_HEAD_YAW_SLIDER, FACE_EDITOR_HEAD_ROLL_SLIDER ])


def remote_update(processors : List[str]) -> Tuple[gradio.Dropdown, gradio.Slider, gradio.Slider, gradio.Slider, gradio.Slider, gradio.Slider, gradio.Slider, gradio.Slider, gradio.Slider, gradio.Slider, gradio.Slider, gradio.Slider, gradio.Slider, gradio.Slider, gradio.Slider]:
	has_face_editor = 'face_editor' in processors
	return gradio.Dropdown(visible = has_face_editor), gradio.Slider(visible = has_face_editor), gradio.Slider(visible = has_face_editor), gradio.Slider(visible = has_face_editor), gradio.Slider(visible = has_face_editor), gradio.Slider(visible = has_face_editor), gradio.Slider(visible = has_face_editor), gradio.Slider(visible = has_face_editor), gradio.Slider(visible = has_face_editor), gradio.Slider(visible = has_face_editor), gradio.Slider(visible = has_face_editor), gradio.Slider(visible = has_face_editor), gradio.Slider(visible = has_face_editor), gradio.Slider(visible = has_face_editor), gradio.Slider(visible = has_face_editor)


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


def update_face_editor_mouth_grim(face_editor_mouth_grim : float) -> None:
	state_manager.set_item('face_editor_mouth_grim', face_editor_mouth_grim)


def update_face_editor_mouth_pout(face_editor_mouth_pout : float) -> None:
	state_manager.set_item('face_editor_mouth_pout', face_editor_mouth_pout)


def update_face_editor_mouth_purse(face_editor_mouth_purse : float) -> None:
	state_manager.set_item('face_editor_mouth_purse', face_editor_mouth_purse)


def update_face_editor_mouth_smile(face_editor_mouth_smile : float) -> None:
	state_manager.set_item('face_editor_mouth_smile', face_editor_mouth_smile)


def update_face_editor_mouth_position_horizontal(face_editor_mouth_position_horizontal : float) -> None:
	state_manager.set_item('face_editor_mouth_position_horizontal', face_editor_mouth_position_horizontal)


def update_face_editor_mouth_position_vertical(face_editor_mouth_position_vertical : float) -> None:
	state_manager.set_item('face_editor_mouth_position_vertical', face_editor_mouth_position_vertical)


def update_face_editor_head_pitch(face_editor_head_pitch : float) -> None:
	state_manager.set_item('face_editor_head_pitch', face_editor_head_pitch)


def update_face_editor_head_yaw(face_editor_head_yaw : float) -> None:
	state_manager.set_item('face_editor_head_yaw', face_editor_head_yaw)


def update_face_editor_head_roll(face_editor_head_roll : float) -> None:
	state_manager.set_item('face_editor_head_roll', face_editor_head_roll)
