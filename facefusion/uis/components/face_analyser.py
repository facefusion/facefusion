from typing import Optional

import gradio

import facefusion.choices
import facefusion.globals
from facefusion import wording
from facefusion.uis.core import register_ui_component

FACE_ANALYSER_DIRECTION_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_ANALYSER_AGE_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_ANALYSER_GENDER_DROPDOWN : Optional[gradio.Dropdown] = None


def render() -> None:
	global FACE_ANALYSER_DIRECTION_DROPDOWN
	global FACE_ANALYSER_AGE_DROPDOWN
	global FACE_ANALYSER_GENDER_DROPDOWN

	FACE_ANALYSER_DIRECTION_DROPDOWN = gradio.Dropdown(
		label = wording.get('face_analyser_direction_dropdown_label'),
		choices = facefusion.choices.face_analyser_directions,
		value = facefusion.globals.face_analyser_direction
	)
	FACE_ANALYSER_AGE_DROPDOWN = gradio.Dropdown(
		label = wording.get('face_analyser_age_dropdown_label'),
		choices = ['none'] + facefusion.choices.face_analyser_ages,
		value = facefusion.globals.face_analyser_age or 'none'
	)
	FACE_ANALYSER_GENDER_DROPDOWN = gradio.Dropdown(
		label = wording.get('face_analyser_gender_dropdown_label'),
		choices = ['none'] + facefusion.choices.face_analyser_genders,
		value = facefusion.globals.face_analyser_gender or 'none'
	)
	register_ui_component('face_analyser_direction_dropdown', FACE_ANALYSER_DIRECTION_DROPDOWN)
	register_ui_component('face_analyser_age_dropdown', FACE_ANALYSER_AGE_DROPDOWN)
	register_ui_component('face_analyser_gender_dropdown', FACE_ANALYSER_GENDER_DROPDOWN)


def listen() -> None:
	FACE_ANALYSER_DIRECTION_DROPDOWN.select(lambda value: update_dropdown('face_analyser_direction', value), inputs = FACE_ANALYSER_DIRECTION_DROPDOWN)
	FACE_ANALYSER_AGE_DROPDOWN.select(lambda value: update_dropdown('face_analyser_age', value), inputs = FACE_ANALYSER_AGE_DROPDOWN)
	FACE_ANALYSER_GENDER_DROPDOWN.select(lambda value: update_dropdown('face_analyser_gender', value), inputs = FACE_ANALYSER_GENDER_DROPDOWN)


def update_dropdown(name : str, value : str) -> None:
	if value == 'none':
		setattr(facefusion.globals, name, None)
	else:
		setattr(facefusion.globals, name, value)
