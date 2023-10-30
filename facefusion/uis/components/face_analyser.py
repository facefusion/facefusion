from typing import Optional

import gradio

import facefusion.globals
import facefusion.choices
from facefusion import wording
from facefusion.typing import FaceAnalyserDirection, FaceAnalyserAge, FaceAnalyserGender
from facefusion.uis.core import register_ui_component

FACE_ANALYSER_DIRECTION_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_ANALYSER_AGE_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_ANALYSER_GENDER_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_DETECTION_SIZE_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_DETECTION_SCORE_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global FACE_ANALYSER_DIRECTION_DROPDOWN
	global FACE_ANALYSER_AGE_DROPDOWN
	global FACE_ANALYSER_GENDER_DROPDOWN
	global FACE_DETECTION_SIZE_DROPDOWN
	global FACE_DETECTION_SCORE_SLIDER

	with gradio.Row():
		FACE_ANALYSER_DIRECTION_DROPDOWN = gradio.Dropdown(
			label = wording.get('face_analyser_direction_dropdown_label'),
			choices = facefusion.choices.face_analyser_directions,
			value = facefusion.globals.face_analyser_direction
		)
		FACE_ANALYSER_AGE_DROPDOWN = gradio.Dropdown(
			label = wording.get('face_analyser_age_dropdown_label'),
			choices = [ 'none' ] + facefusion.choices.face_analyser_ages,
			value = facefusion.globals.face_analyser_age or 'none'
		)
		FACE_ANALYSER_GENDER_DROPDOWN = gradio.Dropdown(
			label = wording.get('face_analyser_gender_dropdown_label'),
			choices = [ 'none' ] + facefusion.choices.face_analyser_genders,
			value = facefusion.globals.face_analyser_gender or 'none'
		)
	FACE_DETECTION_SIZE_DROPDOWN = gradio.Dropdown(
		label = wording.get('face_detection_size_dropdown_label'),
		choices = facefusion.choices.face_detection_sizes,
		value = facefusion.globals.face_detection_size
	)
	FACE_DETECTION_SCORE_SLIDER = gradio.Slider(
		label = wording.get('face_detection_score_slider_label'),
		value = facefusion.globals.face_detection_score,
		step = facefusion.choices.face_detection_score_range[1] - facefusion.choices.face_detection_score_range[0],
		minimum = facefusion.choices.face_detection_score_range[0],
		maximum = facefusion.choices.face_detection_score_range[-1]
	)
	register_ui_component('face_analyser_direction_dropdown', FACE_ANALYSER_DIRECTION_DROPDOWN)
	register_ui_component('face_analyser_age_dropdown', FACE_ANALYSER_AGE_DROPDOWN)
	register_ui_component('face_analyser_gender_dropdown', FACE_ANALYSER_GENDER_DROPDOWN)
	register_ui_component('face_detection_size_dropdown', FACE_DETECTION_SIZE_DROPDOWN)
	register_ui_component('face_detection_score_slider', FACE_DETECTION_SCORE_SLIDER)


def listen() -> None:
	FACE_ANALYSER_DIRECTION_DROPDOWN.select(update_face_analyser_direction, inputs = FACE_ANALYSER_DIRECTION_DROPDOWN)
	FACE_ANALYSER_AGE_DROPDOWN.select(update_face_analyser_age, inputs = FACE_ANALYSER_AGE_DROPDOWN)
	FACE_ANALYSER_GENDER_DROPDOWN.select(update_face_analyser_gender, inputs = FACE_ANALYSER_GENDER_DROPDOWN)
	FACE_DETECTION_SIZE_DROPDOWN.select(update_face_detection_size, inputs = FACE_DETECTION_SIZE_DROPDOWN)
	FACE_DETECTION_SCORE_SLIDER.change(update_face_detection_score, inputs = FACE_DETECTION_SCORE_SLIDER)


def update_face_analyser_direction(face_analyser_direction : FaceAnalyserDirection) -> None:
	facefusion.globals.face_analyser_direction = face_analyser_direction if face_analyser_direction != 'none' else None


def update_face_analyser_age(face_analyser_age : FaceAnalyserAge) -> None:
	facefusion.globals.face_analyser_age = face_analyser_age if face_analyser_age != 'none' else None


def update_face_analyser_gender(face_analyser_gender : FaceAnalyserGender) -> None:
	facefusion.globals.face_analyser_gender = face_analyser_gender if face_analyser_gender != 'none' else None


def update_face_detection_size(face_detection_size : str) -> None:
	facefusion.globals.face_detection_size = face_detection_size


def update_face_detection_score(face_detection_score : float) -> None:
	facefusion.globals.face_detection_score = face_detection_score
